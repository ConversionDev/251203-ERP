import pandas as pd
from typing import Optional
from pathlib import Path


class SeoulDataset:
    _fname: str = '' # file name
    _dname: str = '' # data path
    _sname: str = '' # save path
    _cctv: Optional[pd.DataFrame] = None
    _crime: Optional[pd.DataFrame] = None
    _pop: Optional[pd.DataFrame] = None
    
    def __init__(self):
        """초기화 - 경로 설정"""
        self._dname = str((Path(__file__).parent / "data").resolve())
        self._sname = str((Path(__file__).parent).resolve())

    @property
    def fname(self) -> str: return self._fname

    @fname.setter
    def fname(self, fname): self._fname = fname

    @property
    def dname(self) -> str: return self._dname

    @dname.setter
    def dname(self, dname): self._dname = dname

    @property
    def sname(self) -> str: return self._sname

    @sname.setter
    def sname(self, sname): self._sname = sname

    @property
    def cctv(self) -> Optional[pd.DataFrame]: return self._cctv

    @cctv.setter
    def cctv(self, cctv): self._cctv = cctv

    @property
    def crime(self) -> Optional[pd.DataFrame]: return self._crime

    @crime.setter
    def crime(self, crime): self._crime = crime

    @property
    def pop(self) -> Optional[pd.DataFrame]: return self._pop

    @pop.setter
    def pop(self, pop): self._pop = pop

