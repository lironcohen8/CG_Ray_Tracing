import os
import sys
import numpy as np
from PIL import Image


class Scene:
    def __init__(self, camera, settings, sphere_list, plane_list, box_list, light_list, material_list):
        self.camera = camera
        self.settings = settings
        self.sphere_list = sphere_list
        self.plane_list = plane_list
        self.box_list = box_list
        self.light_list = light_list
        self.material_list = material_list


class Camera:
    def __init__(self, pos, look_at, up_vector, screen_dist, screen_width, screen_height):
        self.pos = pos
        self.look_at = look_at
        self.towards = look_at - pos
        self.up_vector = up_vector
        self.screen_dist = screen_dist
        self.screen_width = screen_width
        self.screen_height = screen_height


class Settings:
    def __init__(self, bg_color, N, max_recursion):
        self.bg_color = bg_color
        self.N = N
        self.max_recursion = max_recursion


class Material:
    def __init__(self, diffuse_color, specular_color, reflection_color, phong_coeff, transparent_val):
        self.diffuse_color = diffuse_color
        self.specular_color = specular_color
        self.reflection_color = reflection_color
        self.phong_coeff = phong_coeff
        self.transparent_val = transparent_val


class Plane:
    def __init__(self, normal_vector, offset, material_idx):
        self.normal_vector = normal_vector
        self.offset = offset
        self.material_idx = material_idx


class Sphere:
    def __init__(self, center_pos, radius, material_idx):
        self.center_pos = center_pos
        self.radius = radius
        self.material_idx = material_idx


class Box:
    def __init__(self, center_pos, edge_len, material_idx):
        self.center_pos = center_pos
        self.edge_len = edge_len
        self.material_idx = material_idx


class Light:
    def __init__(self, pos, color, specular_intens, shadow_intens, light_radius):
        self.pos = pos
        self.color = color
        self.specular_intens = specular_intens
        self.shadow_intens = shadow_intens
        self.light_radius = light_radius


class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = direction

    def compute_point(self, scalar):
        return self.origin + scalar * self.direction


class Screen:
    def __init__(self, corner_pixel, horizontal, vertical):
        self.corner_pixel = corner_pixel
        self.horizontal = horizontal
        self.vertical = vertical


def parse_scene(scene_path, asp_ratio):
    with open(scene_path, 'rb') as f:
        content = f.read()

    material_list = []
    sphere_list = []
    plane_list = []
    light_list = []
    box_list = []
    camera = None
    settings = None
    for line in content.splitlines():
        if len(line) == 0 or line[0] == b'#':
            continue
        line = line.split()
        obj_name = line[0]

        if obj_name == b'cam':
            pos = np.NDarray((float(line[1]), float(line[2]), float(line[3])))
            look_at = np.NDArray((float(line[4]), float(line[5]), float(line[6])))
            up_vector = np.NDArray((float(line[7]), float(line[8]), float(line[9]))) #TODO: Fix the up vector!!!
            screen_dist = float(line[10])
            screen_width = float(line[11])
            screen_height = screen_width * asp_ratio
            camera = Camera(pos, look_at, up_vector, screen_dist, screen_width, screen_height)

        elif obj_name == b'set':
            bg_color = (float(line[1]), float(line[2]), float(line[3]))
            N = float(line[4])
            max_recursion = float(line[5])
            settings = Settings(bg_color, N, max_recursion)

        elif obj_name == b'lgt':
            pos = (float(line[1]), float(line[2]), float(line[3]))
            color = (float(line[4]), float(line[5]), float(line[6]))
            specular_intens = float(line[7])
            shadow_intens = float(line[8])
            light_radius = float(line[9])
            light_list.append(Light(pos, color, specular_intens, shadow_intens, light_radius))

        elif obj_name == b'sph':
            center_pos = (float(line[1]), float(line[2]), float(line[3]))
            radius = float(line[4])
            material_idx = float(line[5])
            sphere_list.append(Sphere(center_pos, radius, material_idx))

        elif obj_name == b'pln':
            normal_vector = (float(line[1]), float(line[2]), float(line[3]))
            offset = float(line[4])
            material_idx = float(line[5])
            plane_list.append(Plane(normal_vector, offset, material_idx))

        elif obj_name == b'box':
            center_pos = (float(line[1]), float(line[2]), float(line[3]))
            edge_len = float(line[4])
            material_idx = float(line[5])
            box_list.append(Box(center_pos, edge_len, material_idx))

        elif obj_name == b'mtl':
            diffuse_col = (float(line[1]), float(line[2]), float(line[3]))
            specular_col = (float(line[4]), float(line[5]), float(line[6]))
            reflection_col = (float(line[7]), float(line[8]), float(line[9]))
            phong_coeff = float(line[10])
            transparent_val = float(line[11])
            material_list.append(Material(diffuse_col, specular_col, reflection_col, phong_coeff, transparent_val))

    scene = Scene(camera, settings, sphere_list, plane_list, box_list, light_list, material_list)
    return scene


def find_sphere_intersect(scene, ray, sphere):
    O = sphere.center_pos
    P0 = scene.camera.pos
    L = O - P0
    V = ray
    r = sphere.radius
    r_squared = r**2

    tca = np.dot(L, V)
    if tca < 0:  # sphere is in the back
        return -1
    d_squared = np.dot(L, L) - tca**2
    if d_squared > r_squared:  # outside of sphere
        return -1
    thc = (r_squared-d_squared)**0.5
    t = tca - thc
    return t


def find_plane_intersect(scene, ray, plane):
    P0 = scene.camera.pos
    N = plane.normal_vector
    d = -1*plane.offset
    V = ray
    t = -1 * (np.dot(P0, N) + d) / np.dot(V, N)
    return t


def find_box_intersect(scene, ray, box):
    pass


def find_min_intersect(scene, ray):
    min_t = -1
    min_surface = None
    for sphere in scene.sphere_list:
        t = find_sphere_intersect(scene, ray, sphere)
        if min_t == -1 or 0 <= t <= min_t:
            min_t = t
            min_surface = sphere

    for plane in scene.plane_list:
        t = find_plane_intersect(scene, ray, plane)
        if min_t == -1 or 0 <= t <= min_t:
            min_t = t
            min_surface = plane

    for box in scene.box_list:
        t = find_box_intersect(scene, ray, box)
        if min_t == -1 or 0 <= t <= min_t:
            min_t = t
            min_surface = box

    min_intersect = ray.compute_point(min_t)
    return min_surface, min_intersect


def save_image(image, output_path):
    img = Image.fromarray(image)
    img.save(output_path)


def construct_pixel_ray(camera, screen, i, j):
    pixel_center = screen.corner_pixel + i * screen.horizontal + j * screen.vertical
    ray_vector = pixel_center - camera.pos
    pixel_ray = Ray(camera.pos, ray_vector)
    return pixel_ray
    #towards = camera.look_at - camera.pos
    #up = camera.up_vector
    #right = np.cross(towards, up)
    #P0 = camera.pos
    #d = camera.screen_dist
    #w = camera.screen_width
    #h = camera.screen_height

    #P_left = P0 + d * towards - (w * right) / 2
    #P_down = P0 + d * towards - (h * up) / 2
    #P = P_left + (j/w + 0.5) * w * right + P_down + (i/h + 0.5) * h * up
    #V = (P-P0) / np.linalg.norm(P-P0)
    #return V


def cross_product(a, b):
    product = (a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0])
    return product


def represent_screen(camera, width_pixels, height_pixels):
    # Determine screen's horizontal, vertical vectors:
    horizontal = cross_product(camera.towards, camera.up_vector)
    vertical = cross_product(camera.towards, horizontal)
    # Determine screen's leftmost bottom pixel (corner pixel):
    left_bottom_pixel = camera.towrads * camera.screen_dist - camera.screen_width/2 * horizontal - camera.screen_height/2 * vertical
    # Normalize screen's horizontal, vertical vectors by pixel's width / height:
    pixel_width = camera.screen_width / width_pixels
    pixel_height = camera.screen_height / height_pixels
    horizontal = pixel_width * horizontal
    vertical = pixel_height * vertical
    # Represent the screen:
    screen = Screen(left_bottom_pixel, horizontal, vertical)
    return screen


def calc_surface_color(scene, surface, min_intersect):
    bg_col = scene.settings.bg_color
    trans_val = (scene.material_list[surface.material_idx]).transparent_val
    diffuse_col = (scene.material_list[surface.material_idx]).diffuse_color
    specular_col = (scene.material_list[surface.material_idx]).specular_color
    reflection_col = (scene.material_list[surface.material_idx]).reflection_color

    output_color = bg_col * trans_val + (diffuse_col + specular_col) * (1 - trans_val) + reflection_col
    return None


def ray_casting(scene, img_width, img_height):
    # TODO: understand if we need to change the matrix coordinate (end of lecture 5)
    image = np.zeros((img_width, img_height, 3), dtype=float)
    screen = represent_screen(scene.camera, img_width, img_height)
    for i in range(img_width):
        for j in range(img_height):
            ray = construct_pixel_ray(scene.camera, screen, i, j)
            surface, min_intersect = find_min_intersect(scene, ray)
            basic_color = calc_surface_color(scene, surface, min_intersect)
            is_lit = trace_light_rays(scene, surface)
            soft_shadow = produce_soft_shadow(scene.surface)
            output_color = calc_output_color()
            image[i, j] = output_color
    save_image(image, output_path)


def main(scene_path, output_path, img_width=500, img_height=500):
    aspect_ratio = img_height/img_width
    scene = parse_scene(scene_path, aspect_ratio)
    ray_casting(scene, img_width, img_height)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])

    if len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])