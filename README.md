
# Vox Cleaner V3
Voxel Model Importer, Cleaner & Exporter, an add-on for Blender 4.2+!
---------------------------------------------------------------------------------------




## How does the cleaning procedure work:

1. **Type Checking & Basic Model fixing** - Remove doubles, etc is done so the model is in cleanable condition
2. **Model Fixing** - The complete model fixing happens here, along with Model duplication. A copy of the model is made so that the colors can be transferred from the copy to the cleaned model.
3. **Material setup** - The materials created & edited based on all the material maps that need to be baked, which are present in the Duplicated model from the Previous step
4. **UV projection** - UVs are projected using Blender's Cube project method and then packed. 
5. **Geo Cleanup** - Blender's Decimate modifier is used to shave off excess geometry. This process destroys the colors on the model.
6. **UV Scaling** - calculation of a rescale factor upto 9 decimals, & then scaling the UVs by the rescale factor to achieve pixel perfect UVs
7. **Texture baking** - using Blender's Cycles render engine. Bakes all the material maps needed
8. **Done! Enjoy!**\
\
\
\
**Shared UV Clean** - All the models are joined, treated as a single Object for the whole process and Split up again. This leads them to have a single baked texture
Besides these, there is a **2-Step Process** that provides more control over the UV process. 

**Batch Cleaning, SubSurface support & Batch Exports** are some extra features that are available in the Pro version as well!

More Information on [My Website ](https://www.thestrokeforge.xyz/vox-cleaner)!
\
\
\
\
\
\
---------------------------------------------------------------------------------------\
Vox Cleaner's Importer is based on a custom, highly modified version of [the importer made by TechnistGuru](https://github.com/technistguru/MagicaVoxel_Importer). Thanks so much! (I tried to thank you personally but no response)

\
**Happy Cleaning! Cheers!** \
**Farhan, The Creator of Vox Cleaner**
