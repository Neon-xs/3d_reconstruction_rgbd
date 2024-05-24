'''
-----------------------------------------------
reconstruction_utilities

Functions for 3d reconstruction.

using opencv3
-----------------------------------------------
'''

import numpy as np
import cv2.aruco as aruco
import numpy as np
import json

from scipy.spatial.transform import Rotation
from scipy.optimize import minimize

# CameraInfo
# class CameraInfo():
#     def __init__(self, width, height, fx, fy, cx, cy, scale):
#         self.width = width
#         self.height = height
#         self.fx = fx
#         self.fy = fy
#         self.cx = cx
#         self.cy = cy
#         self.scale = scale
# END

# read json file
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    return data
# END

# create point cloud from depth image
# def create_point_cloud_from_depth_image(depth, camera, organized=True):
#     assert(depth.shape[0] == camera['height'] and depth.shape[1] == camera['width'])

#     xmap = np.arange(camera['width'])
#     ymap = np.arange(camera['height'])
#     xmap, ymap = np.meshgrid(xmap, ymap)

#     points_z = depth / camera['scale']
#     points_x = (xmap - camera['ppx']) * points_z / camera['fx']
#     points_y = (ymap - camera['ppy']) * points_z / camera['fy']
#     point_cloud = np.stack([points_x, points_y, points_z], axis=-1)

#     if not organized:
#         point_cloud = point_cloud.reshape([-1, 3])

#     pcd = o3d.geometry.PointCloud()
#     pcd.points = o3d.utility.Vector3dVector(point_cloud.astype(np.float32))
#     pcd.colors = o3d.utility.Vector3dVector(point_cloud.astype(np.float32))

#     return pcd
# END

# detect arucomarker position
# def detect_arucomarker_position(arucomarker_image):
#     aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
#     parameters = aruco.DetectorParameters()

#     corners, ids, rejectedImgPoints = aruco.detectMarkers(arucomarker_image, aruco_dict, parameters=parameters)
#     markers_info = list(zip(ids, corners))

#     positions = []

#     for index in range(0, 13):
#         if index in ids:
#             id_index = np.where(ids == index)
#             # print(id_index)

#             marker_id, marker_corners = markers_info[id_index[0][0]]
#             marker_id = np.mean(marker_id)

#             center_x = np.mean(marker_corners[0, :, 0])
#             center_y = np.mean(marker_corners[0, :, 1])

#             positions.append([center_x, center_y])
#         else:
#             positions.append([-1, -1])
    
#     return positions
# END

# get xyz from image pixel
# def get_xyz_from_image_pixal(depth, pixel_x, pixel_y, camera):
#     assert(depth.shape[0] == camera['height'] and depth.shape[1] == camera['width'])

#     point_z = depth[pixel_y, pixel_x] * camera['depth_scale']
#     point_x = (pixel_x - camera['ppx']) * point_z / camera['fx']
#     point_y = (pixel_y - camera['ppy']) * point_z / camera['fy']

#     xyz = [point_x, point_y, point_z]

#     return xyz
# END

# detect arucomarker position 3d
def detect_arucomarker_position_3d(arucomarker_image, depth, camera):
    assert(depth.shape[0] == camera['height'] and depth.shape[1] == camera['width'])

    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
    parameters = aruco.DetectorParameters()

    corners, ids, rejectedImgPoints = aruco.detectMarkers(arucomarker_image, aruco_dict, parameters=parameters)
    
    if ids is None:
        return None
    
    markers_info = list(zip(ids, corners))

    positions = np.zeros([13, 4])

    for index in range(0, 13):
        if index in ids:
            id_index = np.where(ids == index)
            # print(id_index)

            marker_id, marker_corners = markers_info[id_index[0][0]]
            marker_id = np.mean(marker_id)

            center_x = round(np.mean(marker_corners[0, :, 0]))
            center_y = round(np.mean(marker_corners[0, :, 1]))

            # determine 3d position
            point_z = depth[center_y, center_x] * camera['depth_scale']
            point_x = (center_x - camera['ppx']) * point_z / camera['fx']
            point_y = (center_y - camera['ppy']) * point_z / camera['fy']

            positions[index, :] = [point_x, point_y, point_z, 1]
        else:
            positions[index, :] = [-1, -1, -1,  1]
    
    return positions
# END

# register from arucomarker
def register_from_arucomarker(source_amks, target_amks, initial_transform):
    # delete undetected arucomarkers
    rows_to_delete = np.concatenate((np.where(source_amks[:, 0] == -1), np.where(target_amks[:, 0] == -1)), axis=1)[0]
    source_amks = np.delete(source_amks, rows_to_delete, axis=0)
    target_amks = np.delete(target_amks, rows_to_delete, axis=0)

    # error function
    def error_function(trans_params):
        r = Rotation.from_euler('xyz', trans_params[3: 6], degrees=False)

        rotation_matrix = r.as_matrix()

        transform = np.eye(4)
        transform[:3, :3] = rotation_matrix
        transform[:3, 3]  = trans_params[0: 3]
        
        transformed_amks = np.transpose(np.dot(transform, source_amks.T))

        dist  = np.linalg.norm(transformed_amks - target_amks, axis=1)
        error = np.sum(dist) / len(dist)

        return error
    # END
    
    initial_trans_params = initial_transform.flatten()
    result = minimize(error_function, initial_trans_params, method='BFGS', options={'gtol': 1e-3, 'disp': False})

    trans_params = result.x
    r = Rotation.from_euler('xyz', trans_params[3: 6], degrees=False)

    rotation_matrix = r.as_matrix()

    transform = np.eye(4)
    transform[:3, :3] = rotation_matrix
    transform[:3, 3]  = trans_params[0: 3]

    return transform
# END