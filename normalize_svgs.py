from tqdm import tqdm
import os
from deepsvg.svglib.svg import SVG
from glob import glob

input_dir = "/scratch2/moritz_data/fonts/svg/"
classes = os.listdir(input_dir)
print(classes)
output_dir = "/scratch2/moritz_data/google_fonts_normalized/"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

for font_class in tqdm(classes):
    curr_input_dir = os.path.join(input_dir, font_class)
    curr_output_dir = os.path.join(output_dir, font_class)
    if not os.path.exists(curr_output_dir):
        os.makedirs(curr_output_dir)
    for path in glob(curr_input_dir + "/*.svg"):
        output_path = curr_output_dir +"/"+ path.split("/")[-1]
        if os.path.exists(output_path):
            continue
        try:
            my_svg = SVG.load_svg(path)
            for path_group in my_svg:
                path_group.color = "black"
                path_group.fill = True
            my_svg.canonicalize_new(normalize=True).simplify_heuristic().save_svg(output_path)
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                break
            else:
                continue