# F2R

Innocent Grey archieve(.iga) -> Ren'py script(.rpy)

Currently Support:
- FLOWERS Le volume sur printemps
- FLOWERS Le volume sur été
- ~~FLOWERS Le volume sur automne~~
- ~~FLOWERS Le volume sur hiver~~

## Usage

```cmd
python genrpy.py
```
## Todo

 - [] "Boldface Letter" in `dlg_str`(Example:"Heath_" -> "{b}Heath{/b}").
 - [] Mark persistent field in `setVisibleEndCompleted`, `mark_end`, `setGoodEndCompleted`? 
 - [] Implement `play_fg_anim` and `stop_fg_anim`.
 - [] Diference of `scr_eff` Shaking Effect? [Link](https://github.com/zhanghai/igtools/blob/5234750d8e2262d3f922645c37faa64136cfd4eb/igscript/igscript.main.kts#L306)
 - [] Distinguish `jmp_nishuume` between other`jump` instructions.
 - [] Unknown inst in Hiver(`0x57`, `0x5D`, `0x5E`, `0x5F`, `0x60`, `0x61`).

## Reference
Thanks to:
- [shimamura-sakura/FlowerScript](https://github.com/shimamura-sakura/FlowerScript)
- [zhanghai/igtools](https://github.com/zhanghai/igtools)
