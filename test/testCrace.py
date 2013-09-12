import unittest
import numpy as np
import pandas as pd
import scipy
import sys
from pyrace import pnormP, dnormP, LBAAccumulator, Design, \
     StopTaskRaceModel, StopTaskDataSet
from pyrace.models.psslba import pSSLBA_modelA
import pyrace.crace 

class testCRace(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_pnormP(self):
        x=np.linspace(-10,10,100)
        y=pnormP(x)
        y2=np.array([pyrace.crace.pnormP(xx,0,1) for xx in x], dtype=np.double)
        assert np.all( np.abs(y-y2)<1e-9)

        y=pnormP(x, mean=2, sd=3)
        y2=np.array([pyrace.crace.pnormP(xx,2,3) for xx in x], dtype=np.double)
        assert np.all( np.abs(y-y2)<1e-9)

    def test_dnormP(self):
        x=np.linspace(-10,10,100)
        y=dnormP(x)
        y2=np.array([pyrace.crace.dnormP(xx,0,1) for xx in x], dtype=np.double)
        assert np.all( np.abs(y-y2)<1e-9)
        
        y=dnormP(x, mean=2, sd=3)
        y2=np.array([pyrace.crace.dnormP(xx,2,3) for xx in x], dtype=np.double)
        assert np.all( np.abs(y-y2)<1e-9)

    def test_lba_pdf(self):
        acc=LBAAccumulator(.2, .5, 1.0, 1.0, 1.0)
        nsamples=10000
        x=np.linspace(0,10, nsamples)
        y=acc.pdf(x)
        y2=np.array([pyrace.crace.lba_pdf(xx, acc.ter, acc.A, acc.v, acc.sv, acc.b) for xx in x], dtype=np.double)
        assert np.all( np.abs(y-y2)<1e-9)

    def test_lba_cdf(self):
        acc=LBAAccumulator(.2, .5, 1.0, 1.0, 1.0)
        nsamples=10000
        x=np.linspace(0,10, nsamples)
        y=acc.cdf(x)
        y2=np.array([pyrace.crace.lba_cdf(xx, acc.ter, acc.A, acc.v, acc.sv, acc.b) for xx in x], dtype=np.double)
        assert np.all( np.abs(y-y2)<1e-9)
    

    def test_sslba_likelihood_trials(self):
        factors=[{'sleepdep':['normal','deprived']},
                 {'stimulus':['left', 'right']}]
        responses=['left','right']
        design=Design(factors,responses, 'stimulus')
        dat=pd.read_csv('./data/sleep_stop_onesubj_test.csv')
        dat.columns=['sleepdep','stimulus','SSD','response','correct', 'RT']
        ds=StopTaskDataSet(design,dat)

        pars=pSSLBA_modelA.paramspec(.1, .2, .2, .5, .8, 2, 1, 0)
        mod=pSSLBA_modelA(design, pars)
        print mod

        Ls=StopTaskRaceModel.likelihood_trials(mod, ds)
        L2=mod.likelihood_trials(ds)

        goodix=(np.abs(Ls-L2)<1e-5)
        badix=np.logical_not(goodix)
        assert np.sum(badix)==0, "num bad idx=%i"%np.sum(badix)

    def test_loglikelihood(self):
        factors=[{'sleepdep':['normal','deprived']},
                 {'stimulus':['left', 'right']}]
        responses=['left','right']
        design=Design(factors,responses, 'stimulus')
        dat=pd.read_csv('./data/sleep_stop_onesubj_test.csv')
        dat.columns=['sleepdep','stimulus','SSD','response','correct', 'RT']
        ds=StopTaskDataSet(design,dat)

        pars=pSSLBA_modelA.paramspec(.1, .2, .2, .5, .8, 2, 1, 0)        
        mod=pSSLBA_modelA(design, pars)
        print mod

        Ls=StopTaskRaceModel.deviance(mod, ds)
        L2=mod.deviance(ds)
        assert np.abs(Ls-L2)<1e-8
        
if __name__ == '__main__':
    unittest.main()
