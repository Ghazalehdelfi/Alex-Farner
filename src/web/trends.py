from pytrends.request import TrendReq
import pandas as pd

pytrends = TrendReq(hl='en-US', tz=360)
keywords = ["chatgpt"]
pytrends.build_payload(kw_list=keywords, timeframe='today 3-m', geo='')

# print("Interest Over Time:")
# print(pytrends.interest_over_time().head())

# print("\nTop Regions:")
# print(pytrends.interest_by_region(resolution='COUNTRY').sort_values(by=keywords[0],ascending=False).head(5))

r = pytrends.related_queries()
print("\nRelated Queries:", r)
