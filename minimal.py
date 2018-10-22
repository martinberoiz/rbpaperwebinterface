import sys

from django.conf import settings
from django.conf.urls import url
from django.core.management import execute_from_command_line
from django.http import HttpResponse
import numpy as np
import jinja2
import pandas as pd
from bokeh.plotting import figure


settings.configure(
    DEBUG=True,
    SECRET_KEY='d3874a6e97b8cc71e7e177c8d065ead30f67f380c4d9bbadaa',
    ROOT_URLCONF=sys.modules[__name__],
)


template = jinja2.Template("""
<!DOCTYPE html>
<html lang="en-US">

<link
    href="http://cdn.pydata.org/bokeh/release/bokeh-0.13.0.min.css"
    rel="stylesheet" type="text/css"
>
<script src="http://cdn.pydata.org/bokeh/release/bokeh-0.13.0.min.js"></script>

<body>

    <h1>Machine Learning on Difference Image Analysis:</br>A comparison of methods for transient detection</h1>
    
    <p>Title of Histogram</p>
    
    {{ script }}
    
    {{ div }}

</body>

</html>
""")


def plot_figure01(engine):

    simulated = pd.read_sql_query("""SELECT * FROM "Simulated" """, engine)
    hist, edges = np.histogram(simulated['app_mag'], bins=15)
    p = figure(x_axis_label=r'mag', y_axis_label=r'N(m) dm',
               y_axis_type="log",
               tools="save",
              )
    p.quad(top=hist, bottom=0.5, left=edges[:-1], right=edges[1:],
           line_color='black')

    return p


def index(request):
    from bokeh.embed import components
    from sqlalchemy import create_engine

    CONNECTION = "sqlite:///newrbogus-dev.db"
    engine = create_engine(CONNECTION)

    p1 = plot_figure01(engine)

    script, div = components(p1)

    html_page = template.render(script=script, div=div)

    return HttpResponse(html_page)


urlpatterns = [
    url(r'', index),
]

if __name__ == '__main__':
    execute_from_command_line(sys.argv)


