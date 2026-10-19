# Meme SoundFont

把一个 WAV 音效做成 SoundFont 2，用来替换 MIDI 里所有音色。

- **文件**：[`meme_soundfont.sf2`](meme_soundfont.sf2)（77,998 字节）
- **采样**：A#4（MIDI 70），44100 Hz，循环区间 2205–33571
- **覆盖**：bank 0 的 program 0–127 全部指向同一个乐器；另有 bank 128（鼓）一个预设

## 这个库做了什么

MIDI 里每发出一个 Program Change，播放器都会去 SF2 里找对应的预设。
这个库把 **bank 0 的 128 个旋律音色位全部映射到同一个乐器、同一段采样**，
所以任何 MIDI 曲子里所有声部都会变成这个音效。

鼓组（bank 128）单独给了一个预设位，结构上保留，同样指向这段采样。

## 结构

```
RIFF
└─ LIST sfbk
   ├─ LIST INFO      isng / inam
   ├─ LIST sdta
   │  └─ smpl        35,776 个样本（16-bit 单声道）
   └─ LIST pdta
      ├─ phdr        129 个预设 + 终止
      ├─ pbag        130 条
      ├─ pgen        130 条（129 × GEN_INSTRUMENT + 终止）
      ├─ pmod        2 条
      ├─ inst        1 个乐器 + 终止
      ├─ ibag        2 条
      ├─ igen        7 条生成器 + 终止
      ├─ imod        1 条
      └─ shdr        1 个采样头 + 终止
```

索引链：

```
Preset → Bag → Generator → Instrument → Bag → Generator → SampleHeader → PCM
```

乐器层的生成器：

| Gen | 含义 | 值 |
|---|---|---|
| 43 | keyRange | 0–127（所有键共用） |
| 56 | overridingRootKey | 70 |
| 54 | sampleModes | 1（循环） |
| 33 | attack | 约 6 ms |
| 36 | sustain | 0（最大） |
| 37 | release | 约 0.5 s |
| 53 | sampleID | 0 |

## 用法

1. 把 `meme_soundfont.sf2` 放进支持 SoundFont 的 MIDI 播放器
2. 播放任意 MIDI 文件，所有声部都会使用这个音效

## 已知特性

采样是单一音高（A#4）。播放器按「按键音高 ÷ 根音」做变速来实现移调：

- 低于 A#4 的音符 → 放慢 → 音高降低、时长变长
- 高于 A#4 的音符 → 加快 → 音高升高、时长变短

这是 SoundFont 格式的工作方式：**同一个采样在不同音高上，音高和时长必然同时变化**。
如果要让所有音符都保持原始音高与原始速度，需要为每个音高各配一段采样（每根采样把根音设成它自己），
那属于另一种库的构造方式。

## 说明

文件 ID 使用小写 `inam`、长度为奇数，这与 SF2 规范里的
「INFO 子块 ID 大写、字符串长度需为偶数」不完全一致。
实际测试中部分播放器可以正常加载，但**部分解析器（例如 FluidSynth）会拒绝加载**。
如果你遇到加载失败，这通常是第一个需要检查的地方。

## 许可

MIT
