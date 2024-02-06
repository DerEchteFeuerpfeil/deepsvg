from concurrent import futures
import os
from argparse import ArgumentParser
import logging
from tqdm import tqdm
import glob
import pandas as pd

# from deepsvg.svglib.svg import SVG
from deepsvg.svglib.svg import SVG


def preprocess_svg(char_path):
    svg_files = glob.glob(os.path.join(char_path, "**/*.svg"), recursive=True)
    print(f"Found {len(svg_files)} SVG files.")
    meta_data = {}

    for i, svg_path in enumerate(svg_files):
        if i % (len(svg_files) // 10) == 0:
            print(f"Processed {round((i/len(svg_files))*100)}% of {char_path}")
        new_filename = svg_path.replace("/svgs/", "/svgs_simplified/")
        if not os.path.exists(os.path.dirname(new_filename)):
            os.makedirs(os.path.dirname(new_filename))
        if os.path.exists(new_filename):
            continue
        else:
            svg = SVG.load_svg(svg_path)
            svg.fill_(False)
            svg.normalize()
            svg.zoom(0.9)
            svg.canonicalize()
            svg = svg.simplify_heuristic(epsilon=0.001)

            svg.save_svg(new_filename)

            len_groups = [path_group.total_len() for path_group in svg.svg_path_groups]

            meta_data[new_filename] = {
                "id": new_filename.split("/")[-1].split(".")[0],
                "path": new_filename,
                "total_len": sum(len_groups),
                "nb_groups": len(len_groups),
                "len_groups": len_groups,
                "max_len_group": max(len_groups)
            }
    try:
        df = pd.DataFrame(meta_data.values())
        df.to_csv(os.path.join(char_path, "meta_data.csv"), index=False)
    except:
        print(f"Error saving meta_data.csv for {char_path}")

def main(args):
    # each split is handled separately
    # we divide the work into processes, one per character
    for split in ["train", "test"]:
        print(f"Processing {split} split.")
        curr_data_folder = os.path.join(args.data_folder, split)
        with futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
            all_dirs = glob.glob(os.path.join(curr_data_folder, "*"))
            all_dirs = [d for d in all_dirs if os.path.isdir(d)]

            with tqdm(total=len(all_dirs)) as pbar:
                preprocess_requests = [executor.submit(preprocess_svg, char_dir)
                                    for char_dir in all_dirs]

                for _ in futures.as_completed(preprocess_requests):
                    pbar.update(1)

        # df = pd.DataFrame(meta_data.values())
        # if not os.path.exists(os.path.dirname(args.output_meta_file)):
        #     os.makedirs(os.path.dirname(args.output_meta_file))
        # df.to_csv(args.output_meta_file, index=False)

    logging.info("SVG Preprocessing complete.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("--data_folder", default="/scratch2/moritz_data/glyphazzn/svgs")
    parser.add_argument("--workers", default=20, type=int)

    args = parser.parse_args()

    main(args)
