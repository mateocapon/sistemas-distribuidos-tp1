INVALID_YEAR_ID = 0

class Weather:
    def __init__(self, date: str, prectot: str, qv2m: str, rh2m: str,
                 ps: str, t2m_range: str, ts: str, t2mdew: str, t2mwet: str, 
                 t2m_max: str, t2m_min: str, t2m: str, ws50m_range: str, 
                 ws10m_range: str, ws50m_min: str, ws10m_min: str,
                 ws50m_max: str, ws10m_max: str, ws50m: str, ws10m: str, yearid:str):
        self.date = date
        self.prectot = float(prectot)
        self.qv2m = float(qv2m)
        self.rh2m = float(rh2m)
        self.ps = float(ps)
        self.t2m_range = float(t2m_range)
        self.ts = float(ts)
        self.t2mdew = float(t2mdew)
        self.t2mwet = float(t2mwet)
        self.t2m_max = float(t2m_max)
        self.t2m_min = float(t2m_min)
        self.t2m = float(t2m)
        self.ws50m_range = float(ws50m_range)
        self.ws10m_range = float(ws10m_range)
        self.ws50m_min = float(ws50m_min)
        self.ws10m_min = float(ws10m_min)
        self.ws50m_max = float(ws50m_max)
        self.ws10m_max = float(ws10m_max)
        self.ws50m = float(ws50m)
        self.ws10m = float(ws10m)
        self.yearid = int(yearid)
