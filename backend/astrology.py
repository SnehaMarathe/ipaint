import swisseph as swe
from datetime import datetime

def generate_chart(dob,time,place):
 dt=datetime.strptime(dob+" "+time,"%Y-%m-%d %H:%M")
 jd=swe.julday(dt.year,dt.month,dt.day,dt.hour)
 sun=swe.calc_ut(jd,swe.SUN)[0][0]
 moon=swe.calc_ut(jd,swe.MOON)[0][0]
 return {"sun":sun,"moon":moon}