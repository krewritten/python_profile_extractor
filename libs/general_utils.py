from osgeo import ogr
from osgeo import gdalconst
from osgeo import osr
import csv
from shapely.geometry import LineString
from .raster_utils import *
import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
# from dash.dependencies import Input, Output
import os


class ProfileExtractor:
    """
    A class for extracting pixel values from a raster along each vector in a shapefile. The start and end points
    of the line are interpolated at a distance equal to the spatial resolution of the raster.
    No data and 0 values are removed during TIR processing.
    """

    def __init__(self, shp_path, raster_path, raster_driver_name, shp_id_field,
                 shp_front_start_field=None, shp_front_end_field=None, desired_front=None,
                 csv_out_path=None, tir=False):
        """
        The definitions for all inputs in the Profile Extractor class. This is mainly designed to work with fire spread
        vectors and vectors placed in advance of an active front location.
        :param shp_path: path to input shapefile, make sure shapefile is projected in desired CRS
        :param raster_path: path to input raster image, will be reprojected to match shapefile CRS if necessary
        :param raster_driver_name: GDAL driver for raster type
        :param shp_id_field: id field to differentiate each vector in the shapefile
        :param shp_front_start_field: starting fire front
        :param shp_front_end_field: ending fire front
        :param desired_front: if needed to match correct raster during TIR image processing, otherwise None
        :param csv_out_path: out path for csv containing extracted values
        :param tir: set True for vector and thermal infrared imagery work, additional data cleaning and error handling
         measures will be applied.
        """

        self.shp_path = shp_path
        self.raster_path = raster_path
        self.raster_driver_name = raster_driver_name
        self.shp_id_field = shp_id_field
        self.shp_front_start_field = shp_front_start_field
        self.shp_front_end_field = shp_front_end_field
        self.desired_front = desired_front
        self.csv_out_path = csv_out_path
        self.tir = tir

    def print_shp_fields(self):
        """
        This prints the shapefile field names and EPSG and can be useful for correcting input field names when defining
        a class instance
        :return: prints shapefile fieldnames and EPSG
        """
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        path = self.shp_path
        shp = shp_driver.Open(path, 0)
        shp_lyr = shp.GetLayer()
        shp_epsg = shp_lyr.GetSpatialRef()
        shp_epsg_num = shp_epsg.GetAttrValue("Authority", 1)
        shp_def = shp_lyr.GetLayerDefn()
        shp_fields = []
        for i in range(shp_def.GetFieldCount()):
            field_def = shp_def.GetFieldDefn(i)
            shp_fields.append(field_def.name)
        print(shp_fields)
        print("EPSG: {}".format(shp_epsg_num))

    def extractor(self):
        """
        A function to extract pixel values from the input raster and shapefile features
        If self.TIR is True, the TIR processing will be done.
            No data and 0 values will not be included in output shapefile under TIR.
        else: the regular raster processing occurs.
        The Python Geospatial Analysis Cookbook by Michael Diener (2015) was used as a reference for
        concepts on how to create an elevation profile and was the impetus for using Shapely to interpolate LineStrings.
        (url: https://subscription.packtpub.com/book/big_data_and_business_intelligence/9781783555079/7/ch07lvl1sec52/creating-an-elevation-profile)
        :return: outputs a CSV of point values in desired output directory
        """
        # setting up raster based on inputs and raster type
        raster_driver = gdal.GetDriverByName(self.raster_driver_name)
        raster_driver.Register()
        raster = gdal.Open(self.raster_path, gdalconst.GA_ReadOnly)
        raster_proj = osr.SpatialReference(wkt=raster.GetProjection())
        raster_proj_num = raster_proj.GetAttrValue("Authority", 1)

        # setting up shapefile
        shp_driver = ogr.GetDriverByName('ESRI Shapefile')
        path = self.shp_path
        shp = shp_driver.Open(path, 0)
        shp_lyr = shp.GetLayer()
        shp_epsg = shp_lyr.GetSpatialRef()
        shp_epsg_num = shp_epsg.GetAttrValue("Authority", 1)
        # print(shp_epsg_num)

        # checking CRS and reprojecting raster and redefining raster variable if needed
        if raster_proj_num != shp_epsg_num:
            start_end = os.path.split(self.raster_path)
            start_path = start_end[0]
            end_path = "EPSG_" + str(shp_epsg_num) + "_" + start_end[1]
            out_reproj_path = os.path.join(start_path, end_path)
            gdal.Warp(out_reproj_path, self.raster_path, dstSRS=("EPSG:" + str(shp_epsg_num)))
            raster = gdal.Open(out_reproj_path, gdalconst.GA_ReadOnly)
            print("{} reprojected to EPSG: {}".format(self.raster_path, shp_epsg_num))

        # getting x,y of raster
        geo_trans = raster.GetGeoTransform()
        px_w = geo_trans[1]
        if not px_w.is_integer():
            print("WARNING: Shapely interpolation module requires integer input. "
                  "{} spatial resolution ({}) is not an integer. Spatial resolution "
                  "will be rounded to nearest integer; "
                  "consider resampling raster to ensure accurate results.".format(self.raster_path, px_w))

        interp_dist = int(abs(px_w))
        shp_features = shp_lyr.GetNextFeature()
        shp_pts = []
        print("raster loaded")

        if self.tir:  # this option implies they're looking for profiles in advance of one front
            print("TIR Profile Vector Processing")
            while shp_features:
                front_start = shp_features.GetFieldAsString(self.shp_front_start_field)
                shp_geom = shp_features.GetGeometryRef()
                fp = shp_geom.GetPoint(0)
                lp = shp_geom.GetPoint(1)
                line_id = shp_features.GetFieldAsString(self.shp_id_field)
                if int(front_start) == int(self.desired_front):
                    shp_pts.append([line_id, front_start, [fp, lp]])
                shp_features.Destroy()
                shp_features = shp_lyr.GetNextFeature()

            with open(self.csv_out_path, "w", newline="", encoding="utf-8-sig") as out_csv:
                to_csv = csv.writer(out_csv, quoting=csv.QUOTE_NONE)
                to_csv.writerow(["line_id", "front_start", "distance", "x", "y", "pixel_val"])
                for line in shp_pts:
                    ls = LineString(line[2])
                    for i in range(0, int(ls.length), interp_dist):
                        interp = ls.interpolate(i)
                        x_pt, y_pt = interp.x, interp.y
                        z_pt = pixel_values(x_pt, y_pt, raster)  # TIR raster in tens deg C, divide by 10 for deg C
                        try:  # this removes zero values in the TIR imagery
                            if z_pt[0][0] != 0:
                                to_csv.writerow([line[0], line[1], i, x_pt, y_pt, (*z_pt[0] / 10)])
                        except TypeError:
                            print("No data for point index/location ({}, {})".format(x_pt, y_pt))
                out_csv.close()

        else:
            print("Regular Vector Processing")
            while shp_features:
                shp_geom = shp_features.GetGeometryRef()
                fp = shp_geom.GetPoint(0)
                lp = shp_geom.GetPoint(1)
                line_id = shp_features.GetFieldAsString(self.shp_id_field)
                front_start = shp_features.GetFieldAsString(self.shp_front_start_field)
                front_end = shp_features.GetFieldAsString(self.shp_front_end_field)
                ros = shp_features.GetFieldAsString("ros")
                shp_pts.append([line_id, front_start, front_end, ros, [fp, lp]])
                shp_features.Destroy()
                shp_features = shp_lyr.GetNextFeature()

            with open(self.csv_out_path, "w", newline="", encoding="utf-8-sig") as out_csv:
                to_csv = csv.writer(out_csv, quoting=csv.QUOTE_NONE)
                to_csv.writerow(["line_id", "front_start", "front_end", "ros", "distance", "x", "y", "pixel_val"])
                for line in shp_pts:
                    ls = LineString(line[4])
                    for i in range(0, int(ls.length), interp_dist):
                        interp = ls.interpolate(i)
                        x_pt, y_pt = interp.x, interp.y
                        z_pt = pixel_values(x_pt, y_pt, raster)
                        to_csv.writerow([line[0], line[1], line[2], line[3], i, x_pt, y_pt, *z_pt[0]])
                out_csv.close()


class Plotter:
    """
    This class is used to generate the interactive dashboard and data visualizations.
    """

    def __init__(self, input_csv, x, y, color, grouping, hover, title, subtitle=None,
                 plot_type=None, slider_column=None):
        """
        Plotting class to create interactive graphs of profiles using Pandas, Plotly, and Dash.
        :param input_csv: input csv that will be put into pandas data frame
        :param plot_type: line or scatter
        :param x: X variable
        :param y: Y variable
        :param color: field for selecting color, discrete color schemes only for line,
         scatter supports discrete and continuous
        :param grouping: how to group displayed vectors for coloring
        :param hover: field displayed on mouseover
        :param title: Main page title
        :param subtitle: Specific plot title

        """
        self.input_csv = input_csv

        self.x = x
        self.y = y
        self.color = color
        self.grouping = grouping
        self.hover = hover
        self.title = title
        self.subtitle = subtitle



    def create_plot(self):
        """
        the function to actually draw the plot and run a local server displaying the
        interactive data visualizations.
        The Plotly/Dash documentation on lines and plots was used as a reference for this section.
        (url: https://dash.plotly.com/basic-callbacks")
        :return: console log of ip address for local server to access data visualizations
        """
        df = pd.read_csv(self.input_csv)
        # df["ros"] = pd.to_numeric(df["ros"])
        ext_style = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
        app = dash.Dash(__name__, external_stylesheets=ext_style)
        # unique = df.line_id.unique()
        # min_list = df[self.slider_column].min()
        # min = min_list[0]
        # print(avg)
        color_palate = {
            "big-text": "#ffffff",
            "regular-text": "#ffffff",
            "background": "#f5f5f5", # graph background
            "paper": "#121212" #main page background
        }

        plt = px.line(df, x=self.x, y=self.y, color=self.color, line_group=self.grouping, hover_name=self.hover)

        plt.update_layout(
            plot_bgcolor=color_palate["background"],
            paper_bgcolor=color_palate["paper"],
            font_color=color_palate["regular-text"]
        )

        # if self.plot_type == "tir":  # adds additional plot for average profile temperature
        avg = df.groupby("distance", as_index=False).agg("mean")
        avg_plt = px.line(avg, x=avg.distance, y=avg.pixel_val)
        avg_plt.update_layout(
            plot_bgcolor=color_palate["background"],
            paper_bgcolor=color_palate["paper"],
            font_color=color_palate["regular-text"]
        )
        app.layout = html.Div(style={"backgroundColor": color_palate["paper"]},
                              children=[
                                  html.H1(self.title, style={
                                      "color": color_palate["regular-text"]
                                  }),
                                  html.Div(children=self.subtitle, style={
                                      "color": color_palate["regular-text"]
                                  }),
                                  dcc.Graph(
                                      id="plot",
                                      figure=plt
                                  ),
                                  html.Div(children=("Average " + self.subtitle), style={
                                      "color": color_palate["regular-text"]
                                  }),
                                  dcc.Graph(
                                      figure=avg_plt
                                  )
                              ])
        app.run_server(debug=True)
        app.run_server(dev_tools_hot_reload=False)

        # The below code was for a second graph that uses sliders, however there were some internal Dash JavaScript
        # errors with the RangeSlider that could not be resolved.

        # else:
        #     # df = df.set_index("front_end")
        #     app.layout = html.Div(style={"backgroundColor": color_palate["paper"]},
        #                           children=[
        #                               html.H1(self.title, style={
        #                                   "color": color_palate["regular-text"]
        #                               }),
        #                               html.Div(children=self.subtitle, style={
        #                                   "color": color_palate["regular-text"]
        #                               }),
        #                               html.Div([
        #                                   dcc.Graph(
        #                                       id="reg-plot"
        #                                       # figure=plt
        #                                   )
        #                               ]),
        #                               html.Div([
        #                                   dcc.RangeSlider(
        #                                       id="rangeslider",
        #                                       min=df["ros"].min(),
        #                                       max=df["ros"].max(),
        #                                       # value=[df["ros"].min(), df["ros"].max()],
        #                                       value=[df["ros"].min(), df["ros"].max()],
        #                                       step=None,
        #                                       allowCross=True
        #                                   )
        #                               ])
        #
        #                           ])
        #
        #     @app.callback(
        #         Output("reg-plot", "figure"),
        #         [Input("rangeslider", "value")])
        #     def update_plot(val):
        #         # val = "front_start"
        #         print("original")
        #         print(df)
        #         print(val)
        #         print(val[0])
        #         # df_filter = df[(df["ros"] > val[0]) & (df["ros"] < val[1])]
        #         df_filter = df[(df["ros"] < 30)]
        #         print("filtered")
        #         print(df_filter)
        #         print(val[0])
        #         plt2 = px.line(df_filter, x=self.x, y=self.y, color=self.color,
        #         line_group=self.grouping, hover_name=self.hover)
        #         #
        #         # plt2.update_layout(
        #         #     plot_bgcolor=color_palate["background"],
        #         #     paper_bgcolor=color_palate["paper"],
        #         #     font_color=color_palate["regular-text"]
        #         # )
        #         return plt2
        #

