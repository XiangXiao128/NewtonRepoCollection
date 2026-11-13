# Demo Information

<!-- Edit the fields below, then run scripts/build_demos.py (or keep --watch running).
     Description supports **bold** text. Other text fields are plain text.
     Source Repository accepts an HTTP(S) URL.
     Video paths are relative to this info.md. Table row order controls slide order.
     Add or remove video rows when changing the group. -->

## Name
demo02

## Description
A self-contained GPU simulation demo of the Revo3 right hand grasping six YCB objects: apple, orange, banana, tomato soup can, mug and mustard bottle. The five fingertip gels are complete FEM volumes (7,756 nodes / 26,546 tetrahedra), simulated with GPU IPC contact and friction, so the gels visibly deform and each pad reports its contact force. The finger motion is prescribed and each object is held fixed in space. The repo includes a scripted grasp runner, an Isaac Sim path-traced renderer, a grasp planner for adding new YCB objects, and an interactive browser app. In the app, sliders close the fingers, a dropdown switches between the YCB objects, and each pad’s contact force updates live.

## Software Version
Newton 1.6.1, Warp 1.17.0, Isaac Sim 5.1 (rendering only), Python 3.12, viser 1.1.1

## Source Repository
https://github.com/DavidLXu/revo3-ycb-tactile-grasp

## Author
| Name | Homepage | Email |
| --- | --- | --- |
| Lixin Xu | https://davidlxu.github.io | |
| Ke Zhang | http://kezhang19.github.io | |

## Author Homepage
<!-- Individual homepages are recorded in the Author table above. -->

## Author Email
<!-- Add an email address. Used as the author's name link when no homepage is provided. -->

## Videos
| Name | Path |
| --- | --- |
| 01 | 01.mp4 |
| 02 | 02.mp4 |
