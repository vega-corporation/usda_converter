# usda_converter

This is an add-on that can export 3d models by usda file format from blender.

usda is an ASCII file format of the usd format developed by pixar.
if usda converted to usdz, it can be used for AR content on a website and iOS AR apps.
The best way to create usdz is to use [usdz_tools](https://developer.apple.com/augmented-reality/quick-look/) provided by apple.


#### Supported version

blender 2.80 or later

## Install

1. Download the ZIP file first in the "Download ZIP" of right.
2. Click install from add-on menu of the Blender Preferences and select the zip file.
3. Click "usda converter" in the Blender add-on tab of the user settings.

## Usage

The usda export menu is added file menu.
File> Export> Usda (.usda)

## Supported Features

- Meshes
- Animations
- Textures

#### Meshes

Meshes can apply modifiers, triangulation and can include UVs.  
It is recommended to apply triangulation because it may damage the appearance.

#### Animations

Only animations with keyframe input have been verified to work correctly, but the armature is not yet complete.

#### Textures

This add-on can automatically generate texture assets.
When texture option is enabled, the material node tree is scanned and usda compatible PBR materials and textures are created.(Grouped nodes are not yet supported)

## License

This project is licensed under the MIT License.