# Author: Keaton Shennan
# Email: kshennan1233@sdsu.edu
# San Diego State University Department of Geography

# General Notes: Ensure the spatial resolution of the input raster is an integer, otherwise the shapely interpolation
# package will not give consistent results. The local server may take a few seconds to start, try using Chrome if you
# encounter frequent "Unable to Connect" errors in browsers such as Firefox.

from libs.general_utils import *


"""____________________"""


def main():
    # create output directory
    output = "output"
    isdir = os.path.isdir(output)
    if not isdir:
        os.makedirs(output)

    # Two plots are generated to display each possible outcome (TIR profiles or elevation profiles).
    # Comment out one to see the other, as both can not be displayed at the same time.

    ros_vect_elev = ProfileExtractor(shp_path="./data/shp/vectors_ep3.shp",
                                     raster_path="./data/raster/DEM/USGS_NED_13_n35w120_IMG.img",
                                     raster_driver_name="HFA", shp_id_field="vect_id",
                                     shp_front_start_field="vect_front", shp_front_end_field="vect_fro_1",
                                     csv_out_path="./output/ep3_elev_data.csv", desired_front=2, tir=True)

    # ros_vect_elev.print_shp_fields()
    # ros_vect_elev.extractor()

    elev_line = Plotter(input_csv="./output/ep3_elev_data.csv", x="distance",
                        y="pixel_val", color="line_id", grouping="line_id", hover="line_id",
                        title="Elevation Profiles",
                        subtitle="Thomas Fire Seq. 4 Ep. 3 Rate of Spread (ROS) Vector Elevation Profiles")
    # Elevation Profile Plot
    # elev_line.create_plot()

    t1_profile = ProfileExtractor(shp_path="./data/shp/tir_th_seq4_forward_2_5k.shp",
                                  raster_path="./data/raster/TIR/seq4_ep3/2017-12-09-030_IR3_083-te_10mpp.img",
                                  raster_driver_name="HFA", shp_id_field="vect_id",
                                  shp_front_start_field="front", desired_front=2,
                                  csv_out_path="./output/ep3_tir_t1_data.csv", tir=True)

    # t1_profile.print_shp_fields()
    t1_profile.extractor()

    th_ep3_t1_profiles = Plotter(input_csv="./output/ep3_tir_t1_data.csv", x="distance",
                                 y="pixel_val", color="line_id", grouping="line_id", hover="line_id",
                                 title="Thomas Fire Seq. 4 Ep. 3 Temperature Profiles",
                                 subtitle="Temperature profiles in Advance of Active Front ")
    # TIR Profile Plot
    th_ep3_t1_profiles.create_plot()

    t2_profile = ProfileExtractor(shp_path="./data/shp/tir_th_seq4_forward_2_5k.shp",
                                  raster_path="./data/raster/TIR/seq4_ep3/2017-12-09-031_IR3_041-te_10mpp.tif",
                                  raster_driver_name="GTiff", shp_id_field="vect_id",
                                  shp_front_start_field="front", desired_front=3,
                                  csv_out_path="./output/ep3_tir_t2_data.csv", tir=True)

    # t2_profile.extractor()

    t3_profile = ProfileExtractor(shp_path="./data/shp/tir_th_seq4_forward_2_5k.shp",
                                  raster_path="./data/raster/TIR/seq4_ep3/2017-12-09-032_IR3_080-te_10mpp.tif",
                                  raster_driver_name="GTiff", shp_id_field="vect_id",
                                  shp_front_start_field="front", desired_front=3,
                                  csv_out_path="./output/ep3_tir_t3_data.csv", tir=True)

    # t3_profile.extractor()

    t4_profile = ProfileExtractor(shp_path="./data/shp/tir_th_seq4_forward_2_5k.shp",
                                  raster_path="./data/raster/TIR/seq4_ep3/2017-12-09-033_IR3_045-te_10mpp.tif",
                                  raster_driver_name="GTiff", shp_id_field="vect_id",
                                  shp_front_start_field="front", desired_front=3,
                                  csv_out_path="./output/ep3_tir_t4_data.csv", tir=True)

    # t4_profile.extractor()


if __name__ == '__main__':
    main()

"""____________________"""
