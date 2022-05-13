import scene_utils
import intersect

import sys
import numpy as np
import random
from scene_utils import *
from PIL import Image


def construct_pixel_ray(camera, screen, i, j):
    pixel_center = screen.corner_pixel + i * screen.horizontal.dir + j * screen.vertical.dir
    ray_direction = Vector(pixel_center - camera.pos)
    pixel_ray = Ray(camera.pos, ray_direction.dir)
    return pixel_ray


def calc_pixel_color(scene, ray, recursion_depth=0):
    if recursion_depth == scene.settings.max_recursion:
        return scene.settings.bg_color
    surface, min_intersect = intersect.find_min_intersect(scene, ray)
    if surface == None:
        return scene.settings.bg_color
    output_color = calc_surface_color(scene, surface, min_intersect, recursion_depth)
    return output_color


def calc_surface_normal(surface, min_intersect):
    if type(surface) == Sphere:
        return Vector(np.array(min_intersect - surface.center_pos))

    elif type(surface) == Plane:
        return surface.normal_vector

    else:
        pass  # TODO fill


def calc_soft_shadow_fraction(scene, light, min_intersect):
    N = scene.settings.N
    light_ray = Vector(np.array(min_intersect - light.pos))

    # Create perpendicular plane x,y to ray
    x = light_ray.perpendicular_vector()
    y = Vector(np.cross(light_ray.dir, x.dir))

    # Create rectangle
    left_bottom_cell = light.pos - light.light_radius * x.dir - light.light_radius * y.dir

    # Normalize rectangle directions by cell size:
    cell_width = light.light_radius * 2 / N
    cell_height = light.light_radius * 2 / N
    x.dir *= cell_width
    y.dir *= cell_height

    # Cast ray from cell to point and see if intersect with our point first
    intersect_counter = 0
    for i in range(N):
        for j in range(N):
            cell_pos = left_bottom_cell + i * x.dir + j * y.dir
            cell_pos += random.random() * x.dir + random.random() * y.dir
            ray_vector = Vector(np.array(min_intersect - cell_pos))
            cell_light_ray = Ray(light.pos, ray_vector.dir)
            cell_surface, cell_min_intersect = intersect.find_min_intersect(scene, cell_light_ray)
            if (cell_min_intersect == min_intersect).all():
                intersect_counter += 1
    return intersect_counter / (N * N)


def calc_specular_color(scene, light, light_intens, min_intersect, normal, phong_coeff):
    L = Vector(np.array(min_intersect - light.pos))
    R = Vector(L.dir - 2 * np.dot(L.dir, normal.dir) * normal.dir)
    V = Vector(np.array(scene.camera.pos - min_intersect))

    reflection_ray = Ray(min_intersect, R.dir)

    return light.color * light_intens * (np.dot(R.dir, V.dir) ** phong_coeff) * light.specular_intens, reflection_ray


def calc_diffuse_color(light, light_intens, min_intersect, normal):
    light_vector = Vector(np.array(light.pos - min_intersect))
    return light.color * light_intens * np.dot(normal.dir, light_vector.dir)


def calc_surface_color(scene, surface, min_intersect, recursion_depth):
    bg_color = np.array(scene.settings.bg_color)
    trans_value = (scene.material_list[surface.material_idx]).transparent_val
    mat_diffuse = np.array((scene.material_list[surface.material_idx]).diffuse_color)
    mat_specular = np.array((scene.material_list[surface.material_idx]).specular_color)
    mat_reflection = np.array((scene.material_list[surface.material_idx]).reflection_color)
    phong_coeff = (scene.material_list[surface.material_idx]).phong_coeff

    diffuse_color = np.zeros(3, dtype=float)
    specular_color = np.zeros(3, dtype=float)
    reflection_color = np.zeros(3, dtype=float)

    normal = calc_surface_normal(surface, min_intersect)
    for light in scene.light_list:
        # Compute soft shadows fraction
        soft_shadow_frac = calc_soft_shadow_fraction(scene, light, min_intersect)
        light_intens = (1 - light.shadow_intens) + (light.shadow_intens * soft_shadow_frac)

        # Compute light effect on diffuse color
        diffuse_color += calc_diffuse_color(light, light_intens, min_intersect, normal)
        # Compute light effect on specular color
        additive_specular, reflection_ray = calc_specular_color(scene, light, light_intens, min_intersect, normal, phong_coeff)
        specular_color += additive_specular
        # Recursively calc reflection color
        reflection_color += calc_pixel_color(scene, reflection_ray, recursion_depth+1)

    diffuse_color *= mat_diffuse
    specular_color *= mat_specular
    reflection_color *= mat_reflection

    diffuse_color = np.clip(diffuse_color, 0., 1.)
    specular_color = np.clip(specular_color, 0., 1.)
    reflection_color = np.clip(specular_color, 0., 1.)

    output_color = bg_color * trans_value + (diffuse_color + specular_color) * (1 - trans_value) + reflection_color
    return output_color


def save_image(image_array, output_path):
    image_array = 255.*image_array
    print(image_array)
    image = Image.fromarray(image_array.astype('uint8'), 'RGB')
    image.save(output_path)


def ray_tracing(scene, img_width, img_height, output_path):
    image_array = np.zeros((img_width, img_height, 3), dtype=float)
    screen = scene_utils.represent_screen(scene.camera, img_width, img_height)
    for i in range(img_width):
        for j in range(img_height):
            ray = construct_pixel_ray(scene.camera, screen, i, j)
            output_color = calc_pixel_color(scene, ray)
            image_array[j, i] = output_color
    save_image(image_array, output_path)


def main(scene_path, output_path, img_width=500, img_height=500):
    aspect_ratio = img_height/img_width
    scene = scene_utils.parse_scene(scene_path, aspect_ratio)
    ray_tracing(scene, img_width, img_height, output_path)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])

    if len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
