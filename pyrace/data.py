import pandas as pd
import numpy as np
import pylab as pl
import scipy.stats as stats

from tools import *
from design import Design

class StopTaskDataSet(object):
    """
    Implements a data-set for the stop-task.

    
    
    Internally, it stores the data using the following structure:
    
    condition SSD RT response
    
    where condition is an integer number that is expanded by 
    the Design() as is response. 
    
    * if SSD==np.nan -> GO-trial
    * if RT==np.nan -> missed/successful STOP
    * if response==-1 -> miss/successful STOP
    * if condition<0 -> something is wrong with the dataset
    """
    def __init__(self, design, data=None, name=None, format='wide', mapping={'RT':'RT', 'SSD':'SSD', 'response':'response','condition':'condition'}):
        """
        design : Design 
           description of the experiment
        data : pandas.DataFrame or dict
           with columns corresponding to the factors in design (=wide format)
           or with a single 'condition' column indexing design.conditions,
           or dict with fields 'condition', 'RT', 'SSD', 'response' (or a mapping thereof)
        mapping : dict
           must contain keys "RT", "SSD", 'response' and use the values to index into the
           pandas dataframe.
        """
        self.mapping=mapping
        self.design=design
        self.name=name
        if isinstance(data, dict) or format=='dict':
            self.from_dict(data)
        else:
            self.from_pandas_dataframe(data, format=format)

        self.correct=np.zeros_like(self.condition, dtype=np.int)
        for cond in range(self.design.nconditions()):
            corr=self.design.responses.index(self.design.correct_response(cond))
            self.correct[self.condition==cond]=np.where( self.response[self.condition==cond]==corr,  1, 0)

    def from_dict(self, data):
        self.org_data=data
        self.ntrials=len(data[self.mapping['RT']])
        # RT
        self.RT=np.array( data[self.mapping['RT']], dtype=np.float)
        self.RT[np.logical_not(np.isfinite(self.RT))]=np.nan
        
        # SSD
        self.SSD=np.array( data[self.mapping['SSD']], dtype=np.float)
        self.SSD[np.logical_not(np.isfinite(self.SSD))]=np.nan
        
        # responses
        self.response=np.array(data[self.mapping['response']], dtype=np.int)
        if np.any(self.response>=self.design.nresponses()):
            raise ValueError

        # conditions
        self.condition=np.array(data[self.mapping['condition']], dtype=np.int)
        if np.any(self.condition<0) or np.any(self.condition>=self.design.nconditions()):
            raise ValueError
        
    def from_pandas_dataframe( self, data, format="wide"):
        self.org_data=data
        self.ntrials=data.shape[0]

        # RT
        self.RT=np.array( data[self.mapping['RT']], dtype=np.float)
        self.RT[np.logical_not(np.isfinite(self.RT))]=np.nan
        
        # SSD
        self.SSD=np.array( data[self.mapping['SSD']], dtype=np.float)
        self.SSD[np.logical_not(np.isfinite(self.SSD))]=np.nan
        
        # responses
        resp=pd.Categorical.from_array(data[self.mapping['response']])
        if not list_is_eq(resp.levels, self.design.responses):
            raise ValueError('response-array in data.frame does not match design: %s'%str(resp.levels))

        self.response=np.zeros( self.ntrials, dtype=np.int )-1
        for rix,r in enumerate(self.design.responses):
            self.response[resp==r]=rix

        if format=="wide":
            self.from_pandas_dataframe_wide(data)
        elif format=='long':
            self.from_pandas_dataframe_long(data)
        else:
            raise ValueError("unknown format '%s'"%format)
        
    def from_pandas_dataframe_long(self, data):
        # conditions
        self.condition=np.array(data['condition'], dtype=np.int)
        if np.any(self.condition<0) or np.any(self.condition>=self.design.nconditions()):
            raise ValueError
        
    def from_pandas_dataframe_wide(self, data):
        # conditions
        self.condition=np.zeros( self.ntrials, dtype=np.int)-1
        
        for i in range(self.ntrials):
            row=data.irow(i)
            cidx=[row[fac] for fac in self.design.factors]
            self.condition[i]=self.design.condidx(cidx)

    def head(self, n=10, format='wide', conditions_expanded=True):
        return self.as_dataframe(form=format, conditions_expanded=conditions_expanded).head(n)
        
    def as_dataframe(self, form='long', conditions_expanded=True):
        if form=='long':
            if conditions_expanded:
                df=pd.DataFrame({'condition':[":".join(self.design.condidx(c)) for c in self.condition],
                                 'SSD':self.SSD,
                                 'RT':self.RT,
                                 'correct':self.correct,
                                 'response':self.response})
            else:
                df=pd.DataFrame({'condition':self.condition,
                                 'SSD':self.SSD,
                                 'RT':self.RT,
                                 'correct':self.correct,
                                 'response':self.response})
        elif form=='wide':
            df=pd.DataFrame({'SSD':self.SSD,
                             'RT':self.RT,
                             'correct':self.correct,                             
                             'response':self.response})
            for cidx,col in enumerate(self.design.factors):
                df[col]=""
                for i,cond in enumerate(self.condition):
                    df[col].iloc[i]=self.design.condidx(cond)[cidx]
        else:
            raise ValueError("don't know how to handle format %s"%form)
        return df

    def __repr__(self):
        r="{cname}(name={dname},ntrials={ntrials})".format(
            cname=self.__class__.__name__,
            dname=str(self.name),
            ntrials=self.ntrials)
        return r

    def summary(self):
        """
        return summary statistics for the dataset
        """
        r="RT (all): Min=%.2f, Max=%.2f, Mean=%.2f, Median=%.2f\n"%(np.nanmin(self.RT),
                                                                    np.nanmax(self.RT),
                                                                    stats.nanmean(self.RT),
                                                                    stats.nanmedian(self.RT))
        for cond in range(self.design.nconditions()):
            r+="RT ({cond}): Min={minrt}, Max={maxrt}, Mean={maxrt}, Median={medrt}\n".format(
                cond=":".join(self.design.condidx(cond)),
                minrt=np.nanmin(self.RT[self.condition==cond]),
                maxrt=np.nanmax(self.RT[self.condition==cond]),
                meanrt=stats.nanmean(self.RT[self.condition==cond]),
                medrt=stats.nanmedian(self.RT[self.condition==cond]))

        r+='errors (all GO): {nerr}/{ntrials} ({errperc:.2f} %)\n'.format(
            nerr=np.sum(np.logical_not(self.correct[np.isnan(self.SSD)])),
            ntrials=len(self.correct[np.isnan(self.SSD)]),
            errperc=np.sum(np.logical_not(self.correct[np.isnan(self.SSD)]))/float(len(self.correct[np.isnan(self.SSD)])))
        for cond in range(self.design.nconditions()):
            r+='errors ({cond}): {nerr}/{ntrials} ({errperc:.2f} %)\n'.format(
                cond=":".join(self.design.condidx(cond)),
                nerr=np.sum(np.logical_not(self.correct[(self.condition==cond) & np.isnan(self.SSD)])),
                ntrials=len(self.correct[(self.condition==cond) & np.isnan(self.SSD)]),
                errperc=np.sum(np.logical_not(self.correct[(self.condition==cond) & np.isnan(self.SSD)]))
                               /float(len(self.correct[(self.condition==cond) & np.isnan(self.SSD)])))
                
            
        r+='miss GO (all): {nmiss}/{ntrials} ({missperc:.2f} %)\n'.format(
            nmiss=np.sum(np.isnan(self.RT[np.isnan(self.SSD)])),
            ntrials=self.ntrials,
            missperc=100.*np.sum(np.isnan(self.RT[np.isnan(self.SSD)]))/float(self.ntrials)
            )
        for cond in range(self.design.nconditions()):
            r+="miss GO ({cond}): {nmiss}/{ntrials} ({missperc:.2f} %)\n".format(
                cond=":".join(self.design.condidx(cond)),
                ntrials=len(self.RT[self.condition==cond]),
                missperc=100.*np.sum(np.isnan(self.RT[(self.condition==cond) & np.isnan(self.SSD)]))/float(self.ntrials),
                nmiss=np.sum(np.isnan(self.RT[(self.condition==cond) & (np.isnan(self.SSD))])))

        r+="SSD-distribution\n"
        a=stats.itemfreq(self.SSD[np.isfinite(self.SSD)])#.astype(np.int)
        r+= " NUM | "+" ".join(["%7i"%int(i) for i in (a[:,1])]) + "\n"
        r+= " SSD | "+" ".join(["%7.2f"%(i) for i in (a[:,0])]) +"\n"            
        return r
        
    
    def plot_ssd(self, counts=False):
        """plot distribution of SSDs (num samples per SSD)"""
        a=stats.itemfreq(self.SSD[np.isfinite(self.SSD)])#.astype(np.int)
        bw=.01
        if counts==False:
            a[:,1]/=np.sum(a[:,1])
        pl.bar(a[:,0]-bw/2.0, a[:,1], width=bw)
        pl.xlabel('SSD')
        pl.ylabel('freq')
        pl.title('data=%s'%(self.name))        

    def plot_pstop_ssd(self, condition='all', count=False):
        """plot empirical pstop vs. ssd (over all conditions or for a specific one)"""
        bw=.01        
        a=stats.itemfreq(self.SSD[np.isfinite(self.SSD)])#.astype(np.int)
        ssds=a[:,0]
        nssds=a[:,1].astype(np.int)
        pstop=[np.sum(np.isnan(self.RT[self.SSD==ssd]))/float(1.0 if count else nssds[i]) for i,ssd in enumerate(ssds)]
        pl.bar(ssds-bw/2.0, pstop, width=bw)
        pl.title('data=%s, condition=%s'%(self.name,condition))
        pl.xlabel('SSD')
        pl.ylabel('p(STOP)')

    
if __name__=="__main__":
    factors=[{'sleepdep':['normal','deprived']},
             {'stimulus':['left', 'right']}]
    responses=['left','right']
    design=Design(factors,responses, 'stimulus')
    dat=pd.read_csv('./data/sleep_stop_onesubj_test.csv')
    print dat.shape[0]
    dat.columns=['sleepdep','stimulus','SSD','response','correct', 'RT']
    ds=StopTaskDataSet(design,dat)
    print ds.as_dataframe(conditions_expanded=False).head(50)
    print ds.as_dataframe(conditions_expanded=True).head(50)
    print ds.as_dataframe(form='wide', conditions_expanded=True).head(50)
