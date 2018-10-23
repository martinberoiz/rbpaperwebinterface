import sys

from django.conf import settings
from django.conf.urls import url
from django.core.management import execute_from_command_line
from django.http import HttpResponse
import numpy as np
import jinja2
import pandas as pd
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource


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


def make_dataset_fig01(engine):
    simulated = pd.read_sql_query("""SELECT * FROM "Simulated" """, engine)
    hist, edges = np.histogram(simulated['app_mag'], bins=15)
    simulated_mags = pd.DataFrame({'N': hist, 'left': edges[:-1], 'right': edges[1:]})
    simulated_mags['f_N'] = ["{:d}".format(n) for n in simulated_mags['N']]
    simulated_mags['f_interval'] = ["From {:.2f} to {:.2f}".format(l, r)
                                    for l, r in zip(simulated_mags['left'], simulated_mags['right'])]
    return ColumnDataSource(simulated_mags)


def make_plot_fig01(data_src):
    p = figure(plot_width=700, plot_height=700,
               title=r'Simulated Magnitudes',
                  x_axis_label=r'Mags', y_axis_label='N(m) dm',
                  y_axis_type="log",
               tools='save')
    # Quad glyphs to create a histogram
    p.quad(source=data_src, bottom=0.5, top='N', left='left', right='right',
           fill_alpha=0.7, hover_fill_alpha=1.0, line_color='black')

    # Hover tool with vline mode
    hover = HoverTool(tooltips=[('Mag interval', '@f_interval'),
                                ('N', '@f_N')],
                      mode='vline')
    p.add_tools(hover)
    return p


def index(request):
    from bokeh.embed import components
    from sqlalchemy import create_engine

    CONNECTION = "sqlite:///newrbogus-dev.db"
    engine = create_engine(CONNECTION)

    src = make_dataset_fig01(engine)
    p1 = make_plot_fig01(src)

    script, div = components(p1)

    html_page = template.render(script=script, div=div)

    return HttpResponse(html_page)


urlpatterns = [
    url(r'', index),
]


if __name__ == '__main__':
    execute_from_command_line(sys.argv)
