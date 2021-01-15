import sqlite3
import datetime
import calendar
import pandas as pd
import os
from matplotlib.colors import LinearSegmentedColormap

from graph_functions import custom_countplot, cust_heatmap, draw_pie
from send_email import send_mail
import pdfkit


def start_end_weekly():
    now = datetime.datetime.now()
    day_num = now.isoweekday()

    first_wday = now - datetime.timedelta(days=(day_num + 7))
    last_wday = now - datetime.timedelta(days=day_num)
    start = first_wday.strftime("%Y-%m-%d")
    end = last_wday.strftime("%Y-%m-%d")

    # this week (comment out later)
    # end = now + datetime.timedelta(days=(7 - day_num))
    # start = end - datetime.timedelta(days=7)
    # start = start.strftime("%Y-%m-%d")
    # end = end.strftime("%Y-%m-%d")

    return start, end


def start_end_monthly():
    now = datetime.datetime.now()
    if now.month == 1:
        last_month = 12
        year = now.year - 1
    else:
        last_month = now.month - 1
        year = now.year

    first_day, last_day = calendar.monthrange(year, last_month)
    start = datetime.date(now.year, last_month, 1)
    end = datetime.date(now.year, last_month, last_day)

    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")

    return start, end


def pull_data(database, start, end):

    con = sqlite3.connect(database)
    cursor = con.cursor()

    cursor.execute("SELECT * FROM DHCP WHERE date BETWEEN ? AND ?", (start, end))
    data = cursor.fetchall()

    cursor.execute("PRAGMA table_info(DHCP)")
    columns = cursor.fetchall()

    cursor.close()
    con.close()

    cols = [col[1] for col in columns]

    return data, cols


def report(database='', style='weekly'):
    database = database

    if style == 'weekly':
        start, end = start_end_weekly()
    else:
        start, end = start_end_monthly()

    data, columns = pull_data(database=database, start=start, end=end)
    df = pd.DataFrame(data=data, columns=columns)

    # CREATE GRAPHS

    # create colormaps
    color_1 = '#fce100'  # dark yellow
    color_2 = '#000000'  # black
    color_3 = '#606060'  # dark grey
    color_4 = '#a7a7a7'  # light grey
    color_5 = '#ffffff'  # white
    cmap = LinearSegmentedColormap.from_list('yellows', [color_5, color_1])


    # week barchart
    dates = pd.to_datetime(df['date'])
    abbr = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    days = pd.Series([abbr[num] for num in dates.dt.dayofweek])

    dates_c = pd.concat([dates, days], axis=1)
    dates_c = dates_c.set_axis(['date', 'day'], axis=1)

    additions = []
    for day in abbr:
        additions.append((0, day))
    additions = pd.DataFrame(data=additions, columns=['date', 'day'])
    dates_c = pd.concat([dates_c, additions], axis=0)
    dpi_scale = 1

    if not os.path.exists('graphs/'):
        os.mkdir('graphs/')
    # week overview
    week_file = 'graphs/week_file.png'
    custom_countplot(dates_c, 'day', ylabel='Requests', xlabel='Day', title='Week oversight', custom=False, horizontal=False,
                     sort_by_size=False, bar_color=color_1, custom_order_list=abbr, title_clr=color_2, ticklabel_clr=color_3,
                     xlabel_clr=color_4, size=(500, 190), file_name=week_file, dpi_scale=dpi_scale)

    # week heatmap
    heatmap_file = 'graphs/heatmap.png'
    cust_heatmap(df['date'], xlabel_text='', ylabel_text='Hour', cbar_label='Requests', size=(500, 467), cmap=cmap,
                 ticklabel_clr=color_3, label_clr=color_4, cbar_label_clr=color_4, file_name=heatmap_file,
                 dpi_scale=dpi_scale)

    # top 5 hosts count
    tophosts_file = 'graphs/tophosts.png'
    custom_countplot(df, 'hostname', xlabel='DHCP requests', title='Top 10 Hosts', custom=True, horizontal=True,
                     sort_by_size=True, bar_color=color_1, title_clr=color_2, ticklabel_clr=color_3, xlabel_clr=color_4,
                     label_pos_adjustment=(0.73, -0.055), size=(280,450), file_name=tophosts_file, dpi_scale=dpi_scale)

    # vendor pie
    pie_file = 'graphs/pie.png'
    draw_pie(df['vendor'], size=(280, 200), cmap=cmap, text_label_clr=color_3, text_percentage_clr=color_4,
             file_name=pie_file, dpi_scale=dpi_scale)


# yum install wkhtmltopdf
def pdf_from_html():
    html = 'htmls/email_template_for_pdf.html'
    os.makedirs('pdf/', exist_ok=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    image_file_paths = ['graphs/week_file.png', 'graphs/heatmap.png', 'graphs/tophosts.png', 'graphs/pie.png']
    abs_file_paths = [os.path.abspath(f) for f in image_file_paths]
    html_inserts = {
        'week_file': abs_file_paths[0],
        'heatmap': abs_file_paths[1],
        'tophosts': abs_file_paths[2],
        'pie': abs_file_paths[3]
    }
    with open(html, 'r') as html_1:
        html = html_1.read()
        parts = html.split("</style>")
        part_1 = parts[0]
        part_2 = parts[1].format(**html_inserts)
        html_formatted = part_1 + "\n\t</style>\n" + part_2
    formatted_path ='htmls/email_tem_for_pdf_formatted.html'
    with open(formatted_path, 'w') as html_1:
        html_1.write(html_formatted)
    pdf_name = f'pdf/dhcp_report_{now}.pdf'
    pdfkit.from_file(formatted_path, pdf_name)

    return pdf_name


if __name__ == "__main__":

    # CREATE GRAPHS
    report(database='DHCP.db', style='weekly')

    #CREATE PDF FROM HTML
    pdf_name = pdf_from_html()


    # SEND EMAIL
    sender = 'rabbitroger287@gmail.com'
    receivers = ['rabbitroger287@gmail.com', 'niels.worrell@gmail.com']
    username = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PW')

    html_inlined = 'htmls/email_template_inlined.html'
    image_file_paths= ['graphs/week_file.png', 'graphs/heatmap.png', 'graphs/tophosts.png', 'graphs/pie.png']
    html_inserts = {
        'cid1': image_file_paths[0],
        'cid2': image_file_paths[1],
        'cid3': image_file_paths[2],
        'cid4': image_file_paths[3]
    }

    send_mail(subject='Weekly DHCP Requests Report', from_email=sender, to_emails=receivers, user_mailserver=username,
        pw_mailserver=password, html_file_path=html_inlined, html_inserts=html_inserts, att_file_paths=pdf_name)




