# usda_converter

This is an add-on that can export 3d models by usda file format from blender.

usda is an ASCII file format of the usd format developed by pixar.
if usda converted to usdz, it can be used for AR content on a website and iOS AR apps.
The best way to create usdz is to use usdz_tools provided by apple.
[usdz_tools](https://developer.apple.com/augmented-reality/quick-look/)


#### Supported version

blender 2.80 or later

## Install

1. Download the ZIP file first in the "Download ZIP" of right.
2. Click install from add-on menu of the Blender Preferences and select the zip file.
3. Search Start the Blender add-on tab of the user settings in the "usda converter", etc., select the add-on click "save user settings".

## Usage

The usda export menu is added file menu.
File> Export> Usda (.usda)

This exporter supports the following usda features:
- Meshes
- Materials

### Texture conversion

This add-on automatically generates textures that compatible with usda by converting the node tree of the material.

If you don't want to generate different textures, shader uses only the principal shader node and connect the image texture node directly to it.


## License

This project is licensed under the MIT License.