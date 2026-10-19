# v1.0 — Meme SoundFont（全替换音色库）

## 这一版是什么

一个 77,998 字节的 SoundFont 2 文件，把 MIDI 里所有旋律音色替换成同一段音效。

- 采样：A#4（MIDI 70），44100 Hz，循环 2205–33571
- bank 0 的 program 0–127 → 全部指向同一个乐器
- bank 128 保留一个鼓位预设

## 结构

`phdr → pbag → pgen → pmod → inst → ibag → igen → imod → shdr`

- phdr：129 个预设 + 终止记录
- pgen：129 条 GEN_INSTRUMENT + 终止
- igen：keyRange、overridingRootKey、sampleModes、attack、sustain、release、sampleID

## 已知特性

采样只有一个音高（A#4）。播放器通过变速实现移调，所以：

- 低音区音符会变慢、变低沉
- 高音区音符会变快、变尖锐

这是 SoundFont「一个采样对应一个根音」的固有行为。

## 兼容性说明

文件里的 INFO 子块使用了小写 `inam`、且长度为 15 字节。
这与 SF2 规范（ID 大写、长度偶数）不一致。

- 已在部分播放器上验证可正常加载播放
- FluidSynth 会报 `Invalid chunk id in INFO chunk` 并拒绝加载

如果加载失败，优先检查这里：把 `inam` 改成 `INAM`、字符串补到偶数长度即可。

## 怎么用

下载 `meme_soundfont.sf2`，放进支持 SoundFont 的 MIDI 播放器，播放任意 MIDI 即可。
