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
from bokeh.palettes import Category20_16


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
    
    {% for div in divs %}
    {{ div }}
    {% endfor %}

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


def make_dataset_fig02(data_selection, data_fig02, significance_th=-500):

    realbogus_df = pd.DataFrame(columns=['N', 'left', 'right', 'f_N', 'f_interval',
                                         'name', 'color'])

    for i, rb_select in enumerate(data_selection):

        is_real = 1 if rb_select == 'Real' else 0
        dt_src = data_fig02[data_fig02.IS_REAL == is_real].SIGNIFICANCE
        dt_src = dt_src[dt_src > significance_th]
        rb_hist, edges = np.histogram(dt_src, bins=100, range=[-400, 4000])
        rb_df = pd.DataFrame({'N': rb_hist, 'left': edges[:-1], 'right': edges[1:] })
        rb_df['f_N'] = ["{:g}".format(x) for x in rb_df['N']]
        rb_df['f_interval'] = ["{:.1g} to {:.1g}".format(left, right)
                               for left, right in zip(rb_df['left'], rb_df['right'])]
        rb_df['name'] = rb_select
        rb_df['color'] = Category20_16[i]
        realbogus_df = realbogus_df.append(rb_df)

    return ColumnDataSource(realbogus_df)


def make_plot_fig02(src):
        # Blank plot with correct labels
        p = figure(plot_width=700, plot_height=700,
                  title='Real-Bogus Histogram',
                  x_axis_label='Significance', y_axis_label='N',
                  y_axis_type="log")

        # Quad glyphs to create a histogram
        p.quad(source = src, bottom = 0.5, top = 'N', left = 'left', right = 'right',
               color = 'color', fill_alpha = 0.7, hover_fill_color = 'color', legend = 'name',
               hover_fill_alpha = 1.0, line_color = 'black')

        # Hover tool with vline mode
        hover = HoverTool(tooltips=[('Type', '@name'),
                                    ('Significance interval', '@f_interval'),
                                    ('N', '@f_N')],
                          mode='vline')
        p.add_tools(hover)
        p.legend.click_policy = 'hide'

        # Styling
        #p = style(p)

        return p


def index(request):
    from bokeh.embed import components
    from sqlalchemy import create_engine

    CONNECTION = "sqlite:///newrbogus-dev.db"
    engine = create_engine(CONNECTION)

    src = make_dataset_fig01(engine)
    p1 = make_plot_fig01(src)


    data_fig02 = pd.merge(pd.read_sql_table('SCorrDetected', engine),
                      pd.read_sql_query("""SELECT
                                        d.id,
                                        s.app_mag as sim_mag,
                                        s.id as sim_id
                                        FROM "SCorrDetected" d
                                        LEFT JOIN "SCorrReals" r
                                            ON d.id=r.detected_id
                                        LEFT JOIN "Simulated" s
                                            ON s.id=r.simulated_id""", engine),
                                      on='id', suffixes=('',''))

    src = make_dataset_fig02(["Real", "Bogus"], data_fig02)
    p2 = make_plot_fig02(src)

    script, divs = components([p1, p2])

    html_page = template.render(script=script, divs=divs)

    return HttpResponse(html_page)


urlpatterns = [
    url(r'', index),
]


if __name__ == '__main__':
    execute_from_command_line(sys.argv)
