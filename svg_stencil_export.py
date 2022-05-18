#! /usr/bin/env python

import sys
import inkex
import os
import subprocess
import tempfile
import shutil
import copy
import logging
import json

class Options():
    def __init__(self, batch_exporter):

        self.mostLeft = 0
        self.mostRight = 0
        self.mostTop = 0
        self.mostBottom = 0

        self.current_file = batch_exporter.options.input_file

        self.stencil_name = batch_exporter.options.stencil_name
        self.stencil_homepage = batch_exporter.options.stencil_homepage
        self.stencil_author = batch_exporter.options.stencil_author
        self.stencil_description = batch_exporter.options.stencil_description
        self.stencil_license_url = batch_exporter.options.stencil_license_url

        self.create_github_action = self._str_to_bool(batch_exporter.options.create_github_action)
        self.create_gitlab_action = self._str_to_bool(batch_exporter.options.create_gitlab_action)
        self.write_meta = self._str_to_bool(batch_exporter.options.write_meta)
        self.write_components = self._str_to_bool(batch_exporter.options.write_components)
        self.create_cover_page = self._str_to_bool(batch_exporter.options.create_cover_page)
        self.create_readme = self._str_to_bool(batch_exporter.options.create_readme)

        self.export_type = batch_exporter.options.export_type
        self.output_path = os.path.normpath(batch_exporter.options.path)
        self.use_background_layers = self._str_to_bool(batch_exporter.options.use_background_layers)
        self.skip_hidden_layers = self._str_to_bool(batch_exporter.options.skip_hidden_layers)
        self.overwrite_files = self._str_to_bool(batch_exporter.options.overwrite_files)
        self.export_plain_svg = self._str_to_bool(batch_exporter.options.export_plain_svg)
        self.using_clones = self._str_to_bool(batch_exporter.options.using_clones)
        hierarchical_layers = batch_exporter.options.hierarchical_layers
        self.hierarchical_layers = False
        if hierarchical_layers == "hierarchical":
            self.hierarchical_layers = True

        self.export_pdf_version = batch_exporter.options.export_pdf_version

        # Export size page
        self.export_area_type = batch_exporter.options.export_area_type
        self.export_area_size = batch_exporter.options.export_area_size
        self.export_res_type = batch_exporter.options.export_res_type
        self.export_res_dpi = batch_exporter.options.export_res_dpi
        self.export_res_width = batch_exporter.options.export_res_width
        self.export_res_height = batch_exporter.options.export_res_height

        # File naming page
        self.naming_scheme = batch_exporter.options.naming_scheme
        self.use_number_prefix = self._str_to_bool(batch_exporter.options.use_number_prefix)
        self.name_template = batch_exporter.options.name_template

        # Help page
        self.use_logging = self._str_to_bool(batch_exporter.options.use_logging)
        if self.use_logging:
            self.log_path = os.path.expanduser(batch_exporter.options.log_path)
            self.overwrite_log = self._str_to_bool(batch_exporter.options.overwrite_log)
            log_file_name = os.path.join(self.log_path, 'batch_export.log')
            if self.overwrite_log and os.path.exists(log_file_name):
                logging.basicConfig(filename=log_file_name, filemode="w", level=logging.DEBUG)
            else:
                logging.basicConfig(filename=log_file_name, level=logging.DEBUG)

    def __str__(self):
        print =  "===> EXTENSION PARAMETERS\n"
        print += "\n======> Controls page\n"
        print += "Stencil name: {}\n".format(self.stencil_name)
        print += "Current file: {}\n".format(self.current_file)
        print += "Export type: {}\n".format(self.export_type)
        print += "Path: {}\n".format(self.output_path)
        print += "Use background layers: {}\n".format(self.use_background_layers)
        print += "Skip hidden layers: {}\n".format(self.skip_hidden_layers)
        print += "Overwrite files: {}\n".format(self.overwrite_files)
        print += "Export plain SVG: {}\n".format(self.export_plain_svg)
        print += "Using clones: {}\n".format(self.using_clones)
        print += "Hierarchical layers: {}\n".format(self.hierarchical_layers)
        print += "Export PDF version: {}\n".format(self.export_pdf_version)
        print += "\n======> Export size page\n"
        print += "Export area type: {}\n".format(self.export_area_type)
        print += "Export area size: {}\n".format(self.export_area_size)
        print += "Export res type: {}\n".format(self.export_res_type)
        print += "Export res DPI: {}\n".format(self.export_res_dpi)
        print += "Export res width: {}\n".format(self.export_res_width)
        print += "Export res height: {}\n".format(self.export_res_height)
        print += "\n======> File naming page\n"
        print += "Naming scheme: {}\n".format(self.naming_scheme)
        print += "Add number as prefix: {}\n".format(self.use_number_prefix)
        print += "Name template: {}\n".format(self.name_template)
        print += "\n======> Help page\n"
        print += "Use logging: {}\n".format(self.use_logging)
        print += "Overwrite log: {}\n".format(self.overwrite_log)
        print += "Log path: {}\n".format(self.log_path)
        print += "---------------------------------------\n"
        return print

    def _str_to_bool(self, str):
        if str.lower() == 'true':
            return True
        return False

class BatchExporter(inkex.Effect):
    def __init__(self):
        """init the effetc library and get options from gui"""
        inkex.Effect.__init__(self)

        # Controls page
        self.arg_parser.add_argument("--stencil-name", action="store", type=str, dest="stencil_name", default="no-name", help="")
        self.arg_parser.add_argument("--stencil-homepage", action="store", type=str, dest="stencil_homepage", default="", help="")
        self.arg_parser.add_argument("--stencil-author", action="store", type=str, dest="stencil_author", default="", help="")
        self.arg_parser.add_argument("--stencil-description", action="store", type=str, dest="stencil_description", default="", help="")
        self.arg_parser.add_argument("--stencil-license-url", action="store", type=str, dest="stencil_license_url", default="", help="")

        # Controls page
        self.arg_parser.add_argument("--export-type", action="store", type=str, dest="export_type", default="svg", help="")
        self.arg_parser.add_argument("--path", action="store", type=str, dest="path", default="", help="export path")
        self.arg_parser.add_argument("--use-background-layers", action="store", type=str, dest="use_background_layers", default=False, help="")

        self.arg_parser.add_argument("--write-meta", action="store", type=str, dest="write_meta", default=False, help="")
        self.arg_parser.add_argument("--write-components", action="store", type=str, dest="write_components", default=False, help="")
        self.arg_parser.add_argument("--create-github-action", action="store", type=str, dest="create_github_action", default=False, help="")
        self.arg_parser.add_argument("--create-gitlab-action", action="store", type=str, dest="create_gitlab_action", default=False, help="")
        self.arg_parser.add_argument("--create-cover-page", action="store", type=str, dest="create_cover_page", default=False, help="")
        self.arg_parser.add_argument("--create-readme", action="store", type=str, dest="create_readme", default=False, help="")

        self.arg_parser.add_argument("--skip-hidden-layers", action="store", type=str, dest="skip_hidden_layers", default=False, help="")
        self.arg_parser.add_argument("--overwrite-files", action="store", type=str, dest="overwrite_files", default=False, help="")
        self.arg_parser.add_argument("--export-plain-svg", action="store", type=str, dest="export_plain_svg", default=False, help="")
        self.arg_parser.add_argument("--using-clones", action="store", type=str, dest="using_clones", default=False, help="")
        self.arg_parser.add_argument("--hierarchical-layers", action="store", type=str, dest="hierarchical_layers", default="solo", help="Is this working?")
        self.arg_parser.add_argument("--export-pdf-version", action="store", type=str, dest="export_pdf_version", default="1.5", help="")

        # Export size page
        self.arg_parser.add_argument("--export-area-type", action="store", type=str, dest="export_area_type", default="page", help="")
        self.arg_parser.add_argument("--export-area-size", action="store", type=str, dest="export_area_size", default="0:0:100:100", help="")
        self.arg_parser.add_argument("--export-res-type", action="store", type=str, dest="export_res_type", default="default", help="")
        self.arg_parser.add_argument("--export-res-dpi", action="store", type=int, dest="export_res_dpi", default="96", help="")
        self.arg_parser.add_argument("--export-res-width", action="store", type=int, dest="export_res_width", default="100", help="")
        self.arg_parser.add_argument("--export-res-height", action="store", type=int, dest="export_res_height", default="100", help="")

        # File naming page
        self.arg_parser.add_argument("--naming-scheme", action="store", type=str, dest="naming_scheme", default="simple", help="")
        self.arg_parser.add_argument("--use-number-prefix", action="store", type=str, dest="use_number_prefix", default=False, help="")
        self.arg_parser.add_argument("--name-template", action="store", type=str, dest="name_template", default="[LAYER_NAME]", help="")

        # Help page
        self.arg_parser.add_argument("--use-logging", action="store", type=str, dest="use_logging", default=False, help="")
        self.arg_parser.add_argument("--overwrite-log", action="store", type=str, dest="overwrite_log", default=False, help="")
        self.arg_parser.add_argument("--log-path", action="store", type=str, dest="log_path", default="", help="")

        # HACK - the script is called with a "--tab controls" option as an argument from the notebook param in the inx file.
        # This argument is not used in the script. It's purpose is to suppress an error when the script is called.
        self.arg_parser.add_argument("--tab", action="store", type=str, dest="tab", default="controls", help="")


    def effect(self):
        counter = 1

        # Check user options
        options = Options(self)
        logging.debug(options)

        components_list = []
        components_data = {}

        # Build the partial inkscape export command
        command = self.build_partial_command(options)

        # Get the layers from the current file
        layers = self.get_layers(options.skip_hidden_layers, options.use_background_layers)

        # For each layer export a file
        for (layer_id, layer_label, layer_type, parents) in layers:
            if layer_type == "fixed":
                continue

            show_layer_ids = [layer[0] for layer in layers if layer[2] == "fixed" or layer[0] == layer_id]
            # Append parent layers
            if options.hierarchical_layers:
                show_layer_ids.extend(parents)
                logging.debug(show_layer_ids)

            # Create the output folder if it doesn't exist
            if not os.path.exists(os.path.join(options.output_path)):
                os.makedirs(os.path.join(options.output_path))

            # Construct the name of the exported file
            if options.naming_scheme == 'simple':
                file_name = self.get_simple_name(options.use_number_prefix, counter, layer_label)
            else:
                file_name = self.get_advanced_name(options.name_template, counter, layer_label)
            file_name = "{}.{}".format(file_name, options.export_type.lower())
            logging.debug("  File name: {}".format(file_name))

            # Add to components for meta json
            components_list.append(file_name)

            # Check if the file exists. If not, export it.
            destination_path = os.path.join(options.output_path, file_name)
            if not options.overwrite_files and os.path.exists(destination_path):
                logging.debug("  File already exists: {}\n".format(file_name))
                # TODO: Should this be the expected functionality of this scenario?
                counter += 1
                continue

            # Create a new file in which we delete unwanted layers to keep the exported file size to a minimum
            logging.debug("  Preparing layer [{}]".format(layer_label))
            temporary_file = self.manage_layers(layer_id, show_layer_ids, options.hierarchical_layers, options.using_clones)

            components_data[file_name] = {
                    "top": temporary_file['top'],
                    "bottom": temporary_file['bottom'],
                    "left": temporary_file['left'],
                    "right": temporary_file['right']
                    }

            # Export to file
            logging.debug("  Exporting [{}] as {}".format(layer_label, file_name))
            self.export_to_file(command.copy(), temporary_file["name"], destination_path, options.use_logging)

            # Clean up - delete the temporary file we have created
            os.remove(temporary_file["name"])

            counter += 1

        # write_json's
        if options.write_components:
            destination_comp_json = os.path.join(options.output_path, "stencil-components.json")
            stencil_comp_dict = {
                    "components": components_list,
                    "components_data" : components_data
                    }

            with open(destination_comp_json, 'w') as json_file:
                json.dump(stencil_comp_dict, json_file)

        if options.write_meta:
            destination_meta_json = os.path.join(options.output_path, "stencil-meta.json")
            stencil_meta_dict = {
                    "name": options.stencil_name,
                    "author": options.stencil_author,
                    "description": options.stencil_description,
                    "homepage": options.stencil_homepage,
                    "generator": "SVG Stencil Export - Inkscape Extension - Version 1.3",
                    "license": options.stencil_license_url,
                    }

            with open(destination_meta_json, 'w') as json_file:
                json.dump(stencil_meta_dict, json_file)


        if options.create_github_action:
            ghdir = os.path.join(options.output_path, ".github", "workflows" )
            os.makedirs( ghdir, exist_ok=True )

            gh_action_yaml = """name: GitHub Pages

on:
  push:
    branches:
      - main  # Set a branch name to trigger deployment

jobs:
  deploy:
    runs-on: ubuntu-20.04
    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true  # Fetch Hugo themes (true OR recursive)
          fetch-depth: 0    # Fetch all history for .GitInfo and .Lastmod

      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        if: ${{ github.ref == 'refs/heads/main' }}
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: .

"""
            destination_gh_action_yaml = os.path.join(ghdir , "gh-pages.yml")

            ymlfile = open(destination_gh_action_yaml, 'w')
            ymlfile.write(gh_action_yaml)
            ymlfile.close()

        if options.create_gitlab_action:
            gl_action_yaml = """pages:
  stage: deploy
  script:
    - mkdir .public
    - cp -r * .public
    - rm -rf public
    - mv .public public
  artifacts:
    paths:
      - public
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
"""
            destination_gl_action_yaml = os.path.join(options.output_path , ".gitlab-ci.yml")

            ymlfile = open(destination_gl_action_yaml, 'w')
            ymlfile.write(gl_action_yaml)
            ymlfile.close()

        if options.create_readme:

            mddesc = options.stencil_description.replace("\\n","\n")
            indexmd = f"""
# {options.stencil_name}

{mddesc}

Author: {options.stencil_author}

License: {options.stencil_license_url}
"""
            destination_indexmd = os.path.join(options.output_path , "readme.md")

            mdfile = open(destination_indexmd, 'w')
            mdfile.write(indexmd)
            mdfile.close()


        if options.create_cover_page:


            htmldesc = options.stencil_description.replace("\\n","<br>")

            htmljs = '''
  <script>
    switch(window.location.protocol) {
          case 'http:':
          case 'https:':
            document.getElementById('helpText').innerHTML = '<p><a href="https://svg-stencils.github.io/?stencil='+window.location.href+'">preview this stencil in SVG Stencils</a></p><pre style="padding:20px;background-color:#eee; display: inline-block;">{\\n  "name": "'+document.title+'",\\n  "url": "'+window.location.href+'"\\n}</pre><p>Add this stencil to the <a href="https://github.com/svg-stencils/svg-stencils.github.io/edit/main/public/stencils.json">SVG Stencils Library</a> (Only send Pull requests when your Stencil is on a public webserver)</p>'
            break;
            case 'file:':
            document.getElementById('helpText').innerHTML = 'If you run a local webserver you can preview this stencil in <a href="https://svg-stencils.github.io">SVG Stencils</a>. <br>E.g. <strong>cd my-stencil-dir; npm exec http.server -- --cors</strong>'
            break;
            default:
            document.getElementById('helpText').innerHTML = ''
            }
  </script>
            '''


            compstr=""
            for comp in components_list:
                compstr=compstr+'<div class="col-sm"> <img style="max-width:200px;" class="img-thumbnail" src="'+comp+'" /></div>'

            indexhtml = f"""<html>
  <head>
    <title>{options.stencil_name}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
  </head>
  <body>
    <div class="container">
      <div class="row m-3">
        <h1></h1>
        <p>
            Author: {options.stencil_author}<br/>
            <a href="{options.stencil_license_url}">License</a>
        </p>
        <p>{htmldesc}</p>
        <div id="helpText"></div>
      </div>
      <hr>
      <div class="row m-3">
          {compstr}
      </div>
    </div>
    {htmljs}
  </body>
</html>
"""
            destination_indexhtml = os.path.join(options.output_path , "index.html")

            htmlfile = open(destination_indexhtml, 'w')
            htmlfile.write(indexhtml)
            htmlfile.close()


    def get_layers(self, skip_hidden_layers, use_background_layers):
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        layers = []

        for layer in svg_layers:
            label_attrib_name = "{%s}label" % layer.nsmap['inkscape']
            if label_attrib_name not in layer.attrib:
                continue

            # Get layer parents, if any
            parents = []
            parent  = layer.getparent()
            while True:
                if label_attrib_name not in parent.attrib:
                    break
                # Found a parent layer
                # logging.debug("parent: {}".format(parent.attrib["id"]))
                parents.append(parent.attrib["id"])
                parent = parent.getparent()

            # Skipping hidden layers
            if skip_hidden_layers and 'style' in layer.attrib:
                if 'display:none' in layer.attrib['style']:
                    logging.debug("  Skip: [{}]".format(layer.attrib[label_attrib_name]))
                    continue

            layer_id = layer.attrib["id"]
            layer_label = layer.attrib[label_attrib_name]

            # Checking for background (fixed) layers
            if use_background_layers and layer_label.lower().startswith("[fixed] "):
                layer_type = "fixed"
                layer_label = layer_label[8:]
            else:
                layer_type = "export"

            logging.debug("  Use : [{}, {}]".format(layer_label, layer_type))
            layers.append([layer_id, layer_label, layer_type, parents])

        logging.debug("  TOTAL NUMBER OF LAYERS: {}\n".format(len(layers)))
        logging.debug(layers)
        return layers

    def build_partial_command(self, options):
        command = ['inkscape', '--vacuum-defs']

        if options.export_type == 'svg' and options.export_plain_svg == True:
            command.append('--export-plain-svg')
        if options.export_type == 'pdf':
            command.append('--export-pdf-version={}'.format(options.export_pdf_version))

        # Export area - default: export area page
        if options.export_area_type == 'drawing':
            command.append('--export-area-drawing')
        elif options.export_area_type == 'custom':
            command.append('--export-area={}'.format(options.export_area_size))
        else:
            command.append('--export-area-page')

        # Export res - default: no arguments
        if options.export_res_type == 'dpi':
            command.append('--export-dpi={}'.format(options.export_res_dpi))
        elif options.export_res_type == 'size':
            command.append('--export-width={}'.format(options.export_res_width))
            command.append('--export-height={}'.format(options.export_res_height))

        return command

    # Delete/Hide unwanted layers to create a clean svg file that will be exported
    def manage_layers(self, target_layer_id, show_layer_ids, hierarchical_layers, hide_layers):
        # Create a copy of the current document
        doc = copy.deepcopy(self.document)
        target_layer_found = False
        target_layer = None

        # Iterate through all layers in the document
        for layer in doc.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS):
            layer_id = layer.attrib["id"]
            layer_label = layer.attrib["{%s}label" % layer.nsmap['inkscape']]

            # Store the target layer
            if not target_layer_found and layer_id == target_layer_id:
                target_layer = layer
                target_layer_found = True



            # Hide/Delete unwanted layers - hide for use_with_clones = TRUE
            if layer_id not in show_layer_ids:
                if hide_layers:
                    layer.attrib['style'] = 'display:none'
                    logging.debug("    Hiding: [{}, {}]".format(layer_id, layer_label))
                else:
                    layer.getparent().remove(layer)
                    logging.debug("    Deleting: [{}, {}]".format(layer_id, layer_label))

        # Add the target layer as the single layer in the document
        # This option is used, only when all the layers are deleted above
        if not hierarchical_layers:
            root = doc.getroot()
            if target_layer == None:
                logging.debug("    Error: Target layer not found [{}]".format(show_layer_ids[0]))
            target_layer.attrib['style'] = 'display:inline'
            root.append(target_layer)

        self.mostLeft = 0
        self.mostRight = 0
        self.mostTop = 0
        self.mostBottom = 0

        for node in target_layer.iterchildren():
            self.analyseNode(node)

        # Save the data in a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:

            tfile = {
                    "name" : temporary_file.name,
                    "left" : self.makeFloat(self.mostLeft),
                    "top" : self.makeFloat(self.mostTop),
                    "right" : self.makeFloat(self.mostRight),
                    "bottom" : self.makeFloat(self.mostBottom)
                    }


            logging.debug("    Creating temp file {}".format(temporary_file.name))
            doc.write(temporary_file.name)
            return tfile


    def analyseNode(self, node):

        bbox = node.bounding_box()
        if self.mostRight == 0 or (bbox.left + bbox.width) > self.mostRight:
            self.mostRight = bbox.left + bbox.width

        if self.mostBottom == 0 or (bbox.top + bbox.height) > self.mostBottom:
            self.mostBottom = bbox.top + bbox.height

        if self.mostLeft == 0 or bbox.left < self.mostLeft:
            self.mostLeft = bbox.left

        if self.mostTop == 0 or bbox.top < self.mostTop:
            self.mostTop = bbox.top

    def makeFloat(self, var):
        if var is None:
            return 0

        if(type(var) is str):
            arr = var.split(".")
            if(len(arr) > 1):
                var = float(arr[0] +"."+ arr[1])

        return round(float(var),2)

    def imageDim(self, background_image):
        bbox_x = background_image.bounding_box().left
        bbox_y = background_image.bounding_box().top
        bbox_width = background_image.bounding_box().width
        bbox_height = background_image.bounding_box().height



    def get_simple_name(self, use_number_prefix, counter, layer_label):
        if use_number_prefix:
            return "{}_{}".format(counter, layer_label)

        return layer_label

    def get_advanced_name(self, template_name, counter, layer_label):
        file_name = template_name
        file_name = file_name.replace('[LAYER_NAME]', layer_label)
        file_name = file_name.replace("[NUM]", str(counter))
        file_name = file_name.replace("[NUM-1]", str(counter).zfill(1))
        file_name = file_name.replace("[NUM-2]", str(counter).zfill(2))
        file_name = file_name.replace("[NUM-3]", str(counter).zfill(3))
        file_name = file_name.replace("[NUM-4]", str(counter).zfill(4))
        file_name = file_name.replace("[NUM-5]", str(counter).zfill(5))
        return file_name

    def export_to_file(self, command, svg_path, output_path, use_logging):
        command.append('--export-filename=%s' % output_path)
        command.append(svg_path)
        logging.debug("{}\n".format(command))

        try:
            if use_logging:
                # If not piped, stdout and stderr will be showed in an inkscape dialog at the end.
                # Inkscape export will create A LOT of warnings, most of them repeated, and I believe
                # it is pointless to crowd the log file with these warnings.
                with subprocess.Popen(command) as proc:
                    proc.wait(timeout=300)
            else:
                with subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) as proc:
                    proc.wait(timeout=300)
        except OSError:
            logging.debug('Error while exporting file {}.'.format(command))
            inkex.errormsg('Error while exporting file {}.'.format(command))
            exit()

def _main():
    exporter = BatchExporter()
    exporter.run()
    exit()

if __name__ == "__main__":
    _main()
