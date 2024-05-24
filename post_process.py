'''
-----------------------------------------------
post_process

Filter, denoise and convert for point cloud.

using open3d
-----------------------------------------------
'''

import open3d as o3d

# main
def main():
    #####---------- post process ----------#####
    pcd = o3d.io.read_point_cloud("0_reconstruction_001.ply")

    ##### remove plane #####
    # plane_model, plane_inliers = pcd.segment_plane(distance_threshold=0.01, ransac_n=3, num_iterations=1000)

    # pcd_filtered = pcd.select_by_index(plane_inliers, invert=True)

    # o3d.visualization.draw_geometries([pcd_filtered])

    ##### remove noise #####
    pcd_denoised, ids = pcd.remove_statistical_outlier(nb_neighbors=500, std_ratio=0.1, print_progress=True)
    print('Points removed : {:,}'.format(len(ids)))

    ##### convert into mesh #####
    # TO DO

    ##### visualize and save #####
    # o3d.visualization.draw_geometries([pcd])
    o3d.visualization.draw_geometries([pcd_denoised])
    # pcd_denoised = o3d.io.read_point_cloud("0_postprocessed_001.ply")
# END

if __name__ == '__main__':
    print(__doc__)    
    main()
# EOF