from concurrent import futures
import os
from argparse import ArgumentParser
import logging
from tqdm import tqdm
import glob
import pandas as pd

# from deepsvg.svglib.svg import SVG
from deepsvg.svglib.svg import SVG


def preprocess_svg(svg_path, meta_data):

    new_filename = svg_path.replace("/svgs/", "/svgs_simplified/")
    if not os.path.exists(os.path.dirname(new_filename)):
        os.makedirs(os.path.dirname(new_filename))
    if os.path.exists(new_filename):
        return

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


def main(args):
    with futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        svg_files = glob.glob(os.path.join(args.data_folder, "**/*.svg"), recursive=True)
        print(f"Found {len(svg_files)} SVG files.")
        meta_data = {}

        with tqdm(total=len(svg_files)) as pbar:
            preprocess_requests = [executor.submit(preprocess_svg, svg_file, meta_data)
                                    for svg_file in svg_files]

            for _ in futures.as_completed(preprocess_requests):
                pbar.update(1)

    df = pd.DataFrame(meta_data.values())
    if not os.path.exists(os.path.dirname(args.output_meta_file)):
        os.makedirs(os.path.dirname(args.output_meta_file))
    df.to_csv(args.output_meta_file, index=False)

    logging.info("SVG Preprocessing complete.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser()
    parser.add_argument("--data_folder", default="/scratch2/moritz_data/glyphazzn/svgs")
    parser.add_argument("--output_meta_file", default="/scratch2/moritz_data/glyphazzn/svgs_simplified/svg_meta.csv")
    parser.add_argument("--workers", default=32, type=int)

    args = parser.parse_args()

    main(args)
