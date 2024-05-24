'''
-----------------------------------------------
3d_reconstruction_rgbd

Reconstruction, registration and merging from RGBD images.

using opencv3, open3d
      3d_reconstruction_utilities.py
      progress_bar.py
-----------------------------------------------
'''

import numpy as np
import open3d as o3d
import cv2
import numpy as np

from progress_bar import BarMod
from reconstruction_utilities import *

# main
def main():
    image_num = 80

    camera = read_json_file('intrinsics.json')
    camera_intrinsic = o3d.io.read_pinhole_camera_intrinsic('camera_primesense.json')
    
    #####---------- reconstruction ----------#####
    bar = BarMod('Reconstruct from RBGD:', max=image_num)
    failed_id = []
    
    for index in range(0, image_num + 1):
        # progress bar
        bar.next()
        
        ##### image to point cloud #####
        color_file_path = 'color/' + str(index) + '.jpg'
        depth_file_path = 'depth/' + str(index) + '.png'

        color_cv2 = cv2.imread(color_file_path)
        depth_cv2 = cv2.imread(depth_file_path,cv2.IMREAD_ANYDEPTH)

        color_o3d = o3d.io.read_image(color_file_path)
        depth_o3d = o3d.io.read_image(depth_file_path)
        depth_scale = 1 / camera['depth_scale']

        source_rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color_o3d, depth_o3d, depth_scale, convert_rgb_to_intensity=False)
        source_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(source_rgbd_image, camera_intrinsic)
        
        # filter
        plane_model, plane_inliers = source_pcd.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=1000)
        source_pcd = source_pcd.select_by_index(plane_inliers, invert=True)

        ##### merge #####
        if index != 0:
            ##### rotate from QR code #####
            # TO DO
            # odo_init = np.identity(4)

            source_amk_positions = detect_arucomarker_position_3d(cv2.cvtColor(color_cv2, cv2.COLOR_BGR2GRAY), depth_cv2, camera)
            
            if source_amk_positions is None:
                failed_id.append(index)
                continue

            odo_init = register_from_arucomarker(source_amk_positions, amk_positions, odo_init)

            ##### odometry and merge #####
            # option = o3d.pipelines.odometry.OdometryOption()
            # option.depth_diff_max = 0.0025
            
            # # [success, transform, info] = o3d.pipelines.odometry.compute_rgbd_odometry(
            # #     source_rgbd_image, rgbd_image, camera_intrinsic, odo_init,
            # #     o3d.pipelines.odometry.RGBDOdometryJacobianFromColorTerm(), option)
            # [success, transform, info] = o3d.pipelines.odometry.compute_rgbd_odometry(
            #     source_rgbd_image, rgbd_image, camera_intrinsic, odo_init,
            #     o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(), option)
            
            source_pcd.transform(odo_init)
            pcd += source_pcd
        else:
            amk_positions = detect_arucomarker_position_3d(cv2.cvtColor(color_cv2, cv2.COLOR_BGR2GRAY), depth_cv2, camera)
            odo_init = np.identity(4)

            rgbd_image = source_rgbd_image
            pcd = source_pcd

    bar.finish()

    if len(failed_id) > 0:
        print('Images failed to register: {}'.format(failed_id))
    
    ##### visualize and save #####
    o3d.visualization.draw_geometries([pcd])
    # o3d.io.write_point_cloud("0_reconstruction_1.ply", pcd)
    
    # #####---------- post process ----------#####
    # Moved to post_process.py
# END


if __name__ == '__main__':
    print(__doc__)    
    main()
# EOF