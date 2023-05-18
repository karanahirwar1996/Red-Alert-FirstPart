import smtplib
from email.mime.text import MIMEText
import datetime
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download the Vader lexicon
nltk.download('vader_lexicon')
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
def short_link(link):
    import urllib.parse
    import urllib.request

# Define the URL shortening service endpoint and long URL to be shortened
    endpoint = 'http://tinyurl.com/api-create.php'
    long_url = link
# Encode the long URL as a query parameter for the API call
    params = {'url': long_url}
    encoded_params = urllib.parse.urlencode(params).encode('utf-8')

# Make the API call and check the response status code
    response = urllib.request.urlopen(endpoint + '?' + encoded_params.decode('utf-8'))
    if response.status == 200:
        short_url = response.read().decode('utf-8')
        return short_url
    else:
        return 'Error: HTTP'
def parse_date(date_string):
    return datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").date()
def parse_time(date_string):
    import datetime
    parsed_time = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ").time()
    formatted_time = parsed_time.strftime("%-I:%M%p")
    return formatted_time

def analyze_sentiment(text):
    sid = SentimentIntensityAnalyzer()
    sentiment_scores = sid.polarity_scores(text)
    return sentiment_scores['compound']

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import datetime

def stock_details(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content, features="html.parser")
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if script_tag is None:
        print(f"No script tag with id '__NEXT_DATA__' found on {url}")
        return None
    json_data = json.loads(script_tag.string)
    security_info = json_data['props']['pageProps'].get('securityInfo', None)
    if security_info is None:
        print("No security info found.")
        return None
    info = security_info.get('info', {})
    isin = security_info.get('isin', None)
    name = info.get('name', None)
    sector = info.get('sector', None)
    value = security_info.get('ratios', {})
    change = json_data['props']['pageProps']['securityQuote'].get('dyChange', None)
    wk = json_data['props']['pageProps']['securityQuote'].get('wkChange', None)
    _52whigh = value.get('52wHigh', None)
    _52wlow = value.get('52wLow', None)
    details = json_data['props']['pageProps']['securityQuote']
    price = details.get('price', None)
    date_today = datetime.date.today().strftime('%Y-%m-%d')
    data = {'Date': date_today, 'Name': name, 'ISIN': isin, 'Sector': sector, '52 Week High': _52whigh, '52 Week Low': _52wlow, 'Day Return': change, 'Week Return': wk, 'Price': price, "URL": url}
    df = pd.DataFrame(data, index=[0])
    under2000 = df.loc[(df['Week Return'] > 2)&(df['Price'] < 2000)]
    under2000['New_URL'] = under2000['URL'].apply(short_link)
    if len(under2000) > 0:
        res = requests.get(under2000['URL'][0])
        soup = BeautifulSoup(res.content, features="html.parser")
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        json_data = json.loads(script_tag.string)
        news = json_data['props']['pageProps']['securitySummary'].get('news', None)
        financial = None
        if 'financialSummary' in json_data['props']['pageProps']['securitySummary']:
            financial = pd.DataFrame(json_data['props']['pageProps']['securitySummary']['financialSummary']['fiscalYearToData'])
        if news:
            news_df = pd.DataFrame(news, columns=['headline', 'date', 'link'])
            news_df['Date'] = news_df['date'].apply(parse_date)
            news_df['Time'] = news_df['date'].apply(parse_time)
            news_df=news_df[['headline', 'Date','Time','link']]
            # Filter news for today and yesterday
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            news_df = news_df[(news_df['Date'] == today) | (news_df['Date'] == yesterday)]

            # Perform sentiment analysis
            news_df['sentiment_score'] = news_df['headline'].apply(analyze_sentiment)
            positive_news_df = news_df[news_df['sentiment_score'] > 0.7]

            if len(positive_news_df) >= 1:
                positive_news_df = positive_news_df.sort_values('Date', ascending=False)
                last_two_dates = positive_news_df['Date'].unique()[:2]
                filtered_news_df = positive_news_df[positive_news_df['Date'].isin(last_two_dates)]
                news_table_html = filtered_news_df.to_html(index=False)

# Create the email message
                sender_email = "karan.ahirwar1996@gmail.com"
                receiver_email = list(pd.read_csv("./emaillist.csv")['mail'])
                password = "uccrgtqdnusrpmnk"

                table_html = under2000[["ISIN",'Name', 'Price','52 Week Low','52 Week High', 'Week Return', 'New_URL']].to_html(index=False)
                if financial is None:
                            financial_html = None
                else:
                            financial_html = financial.to_html(index=False)

                message = MIMEText(f"""
<html>
  <head>
    <style>
      body {{
        font-family: Arial, sans-serif;
        font-size: 16px;
        line-height: 1.5;
        color: black;
      }}
      
      table {{
        border-collapse: collapse;
        width: 100%;
      }}
      
      th, td {{
        border: 1px solid #dddddd; /* Set table border color */
        padding: 8px;
        text-align: left;
      }}
      
      th {{
        background-color: #f2f2f2; /* Set table header background color */
        color: #333333;
        font-weight: bold;
      }}
      
      h2 {{
        margin-bottom: 12px;
        color: #333333; /* Set heading text color */
      }}
      
      p {{
        margin-bottom: 20px;
      }}
    </style>
  </head>
  <body>
    <h2>Stock Details - {under2000['Name'].values[0]}</h2>
    <p>Hey ,</p>
    <p>I hope this email finds you well. I am writing to inform you about a recent development regarding stocks. As of today, there have been significant changes in the stock market. The details for  {under2000['Name'].values[0]} are as follows:</p>
    {table_html}
    <p>Additionally, I would like to inform you that there have been positive news articles related to {under2000['Name'].values[0]} in the past two days. This suggests that there might be an increased chance of the stock prices rising. Here are the details of the positive news articles:</p>
    {news_table_html}
    <p>Here are the fiscal year details for {under2000['Name'].values[0]}:</p>
    {financial_html}
    <p>Best regards,<br>Karan Ahirwar</p>
  </body>
</html>
""", "html")


                message["Subject"] = f"Stock Details-{under2000['Name'].values[0]}"
                message["From"] = sender_email
                message["To"] = ", ".join(receiver_email)

# Send the email
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                            server.login(sender_email, password)
                            server.sendmail(sender_email, receiver_email, message.as_string())

    return df

url_df=pd.read_csv("./Allstockurl.csv")
url_list=list(url_df['URL'])[0:750]
df_list = []
for i, url in enumerate(url_list):
    df1 = stock_details(url)
    df_list.append(df1)
    if (i + 1) % 400 ==0:
        print(f"Processed {i + 1} URLs. Sleeping for 3 seconds...")
        time.sleep(3)
result_df = pd.concat(df_list,ignore_index=True)
