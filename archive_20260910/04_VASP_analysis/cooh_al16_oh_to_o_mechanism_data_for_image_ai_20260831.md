# CoOOH 中 Al 邻位替换影响 *OH -> *O 的机理与数值资料

用途：供 ChatGPT Image 2 或其他科学绘图 AI 阅读，用于生成论文中的机理示意图。  
数据状态日期：2026-08-31。  
核心比较：未掺杂 `*OH-Co-O-Co` 与邻位 Al 替换后的 `*OH-Co-O-Al`。  
反应范围：只采用传统四步 AEM/CHE；重点为第二步 `*OH -> *O + H+ + e-`。

---

## 1. 必须首先理解的结论

1. 实验事实和已完成热化学都把关键问题指向 `*OH -> *O`。
2. Al 不是简单地向活性 Co 大量供电子，也不是对所有 OER 中间体产生同方向的均匀吸电子效应。
3. cDFT 最清楚的结果是：未掺杂体系在 `*OH -> *O` 时活性 Co 参与明显电荷和自旋重排；Al16 中活性 Co 的局域电荷响应被强烈缓冲，而吸附 O 承担更显著的自旋响应并发生自旋符号反转。
4. VASP-Bader 的最终基态净电荷变化较小，且活性 Co 在两种体系中都只增加约 `0.03 e`。这不否定 cDFT，因为两者测量对象不同：cDFT 测局域受限响应，Bader 测最终基态拓扑分区后的净电荷。
5. LOBSTER 轨道布居表明，`*OH -> *O` 的净氧化主要表现为 Oads 2p 少数自旋电子减少，同时 Oads 2p 多数自旋占据有所增加。因此必须把两个过程分开画：
   - 蓝色少数自旋：O 中心净失电子，进入外电路。
   - 橙色多数自旋：Co-O 成键重杂化和磁交换响应。
6. COHP 的跨材料差异几乎全部来自多数自旋成键通道：
   - 未掺杂多数自旋 `Delta(-ICOHP) = 0.56027 eV`。
   - Al16 多数自旋 `Delta(-ICOHP) = 0.20887 eV`。
   - 少数自旋分别为 `0.90463` 和 `0.90347 eV`，近乎不变。
7. 因此最稳妥的机理表述是：

> 邻位 Co 被近似非磁性的 Al 替换后，原有的 O 介导 Co-O-Co 磁性交换和多数自旋 Co-O 重杂化被削弱。去质子化仍以 O 中心少数自旋电子移除为主，但活性 Co 的自旋重组减小，氧化和自旋响应更集中在吸附 O 上。

8. 该机理与实验“Al 有利于 *OH 到 *O”方向一致，但最终覆盖度依赖 CHE 脱质子电位仍在计算，不能把尚未完成的电位序列画成已验证结果。

---

## 2. 数据定义和符号

- `N` 或 `population`：原子/轨道电子数。`Delta N > 0` 表示得到电子。
- `q`：净原子电荷。`Delta q > 0` 表示失电子。
- `m`：沿全局量子化轴的局域磁矩；正负号表示自旋方向，不等同于氧化态。
- `spin 1`：在本计算的活性 Co 上对应多数自旋通道。
- `spin 2`：在本计算的活性 Co 上对应少数自旋通道。
- `ICOHP < 0`：成键。数值越负，积分成键越强。
- `Delta ICOHP = ICOHP(*O) - ICOHP(*OH)`；负值表示从 *OH 到 *O 成键增强。
- `Delta(-ICOHP) = -Delta ICOHP`；正值越大表示成键增强幅度越大。
- cDFT、Bader、Mulliken、Lowdin 和 Hirshfeld 是不同分区/约束定义，绝不能把数值直接相加。
- 所有 cDFT 罚能均为固定几何局域化能，不是 CHE 自由能，也不是动力学能垒。
- 所有正式 Bader/COHP OH/O 对比均为匹配固定几何电子效应计算；最终完全弛豫结构效应仍应单独讨论。

---

## 3. 模型、构型和原子编号

### 3.1 cDFT/CP2K 模型

| 体系 | 构型 | 活性 Co | 活性 H | 吸附 O/Oads | 第二 O |
|---|---|---:|---:|---:|---:|
| Undoped | OH | Co32 | H211 | O212 | - |
| Undoped | O | Co32 | - | O211 | - |
| Undoped | OOH | Co32 | H211 | O212 | O213 |
| Al16 | OH | Co48 | H221 | O222 | - |
| Al16 | O | Co48 | - | O221 | - |
| Al16 | OOH | Co48 | H221 | O222 | O223 |

注意：cDFT 的 accepted undoped Co32 与 Al16 Co48 化学上有效，但局部几何不是严格同一位点，适合机理比较，不适合作为精确匹配势垒。

### 3.2 VASP 固定几何 OH/O 模型

| 体系 | 构型 | Coact | 邻位金属 | Oads | Obridge | 邻位 OH 的 O | 邻位 OH 的 H |
|---|---|---:|---:|---:|---:|---:|---:|
| Undoped | OH | Co21 | Co23 | O348 | O259 | O260 | H116 |
| Undoped | O | Co21 | Co23 | O347 | O258 | O259 | H116 |
| Al16 | OH | Co16 | Al51 | O348 | O259 | O260 | H116 |
| Al16 | O | Co16 | Al51 | O347 | O258 | O259 | H116 |

OH 到 O 时移除活性 H204，使后续 O 的 VASP 原子编号统一减 1；表中不同编号对应相同物理原子。

### 3.3 价电子参考数

- Co：9 个价电子，Bader 净电荷 `q = 9 - N_Bader`。
- Al：3 个价电子，`q = 3 - N_Bader`。
- O：6 个价电子，`q = 6 - N_Bader`。
- H：1 个价电子，`q = 1 - N_Bader`。

---

## 4. 传统四步 AEM/CHE

1. `* + H2O -> *OH + H+ + e-`
2. `*OH -> *O + H+ + e-`
3. `*O + H2O -> *OOH + H+ + e-`
4. `*OOH -> * + O2 + H+ + e-`

### 4.1 已验证严格未掺杂 298.15 K CHE

| 步骤 | 反应 | Delta G / eV |
|---:|---|---:|
| 1 | `* -> *OH` | 1.755822390 |
| 2 | `*OH -> *O` | 2.030710620 |
| 3 | `*O -> *OOH` | 0.669871268 |
| 4 | `*OOH -> * + O2` | 0.463595722 |

- PDS：`*OH -> *O`。
- limiting potential：`2.030710620 V`。
- overpotential：`0.800710620 V`。
- 状态：`VALID_STRICT_THERMO`。

### 4.2 历史 CP2K 电子自由能台阶，仅作趋势参考

| 体系 | dG1 | dG2: OH->O | dG3 | dG4 | 单位 |
|---|---:|---:|---:|---:|---|
| Undoped Co32 | 1.199993 | 1.793143 | 1.534211 | 0.392652 | eV |
| Al16 Co7_adjAl | 1.403097 | 1.524802 | 0.871955 | 1.120146 | eV |
| Al16 Al47 active site | 2.382189 | -1.011081 | 2.217542 | 1.331350 | eV |

历史相邻 Al 的 Co 活性位使 OH->O 从 `1.793143` 降至 `1.524802 eV`，差值 `-0.268341 eV`。不同模型和位点不能当作最终严格匹配结果。

### 4.3 固定几何第一脱质子电位，初步值

| 体系 | Ueq electronic / V | 298.15 K local correction / eV | Ueq 298.15 K CHE / V | 状态 |
|---|---:|---:|---:|---|
| Undoped | 3.05451352 | -0.32469534 | 2.72981818 | preliminary |
| Al16 | 2.39551352 | -0.32469534 | 2.07081818 | preliminary |

初步差值 `Al16 - undoped = -0.65900000 V`，与实验方向一致，但这是固定几何第一脱质子近似，不是最终覆盖度依赖 S13/CHE 结果。

### 4.4 尚未完成

- S13 风格 terminal-OH 覆盖度去质子阵列 `111357` 尚未给出完整有效序列。
- 最终应报告每个 `U_i`、半覆盖电位和 Frumkin width。
- 绘图 AI 不得在正式机理图中写入一个“最终 Al 降低电位”的确定数值；如必须标注，只能写 `preliminary fixed-geometry: -0.659 V`。

---

## 5. cDFT 基线原子电荷和自旋

### 5.1 所有 OH/O/OOH 相关原子

| 体系 | 构型 | 原子 | Mulliken N | Mulliken q | Mulliken m | Hirshfeld N | Hirshfeld q | Hirshfeld m |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Undoped | OH | Co32 | 16.142444 | +0.857556 | +3.254625 | 18.355 | -1.356 | +3.215 |
| Undoped | OH | H211 | 0.647927 | +0.352074 | +0.003589 | 0.407 | +0.593 | +0.003 |
| Undoped | OH | O212 | 6.425180 | -0.425180 | +0.627114 | 6.141 | -0.141 | +0.607 |
| Undoped | O | Co32 | 16.289636 | +0.710365 | +2.454644 | 18.574 | -1.574 | +2.394 |
| Undoped | O | O211 | 6.282797 | -0.282797 | +0.564299 | 5.677 | +0.324 | +0.537 |
| Undoped | OOH | Co32 | 16.130767 | +0.869233 | +3.247431 | 18.281 | -1.281 | +3.176 |
| Undoped | OOH | H211 | 0.691227 | +0.308773 | -0.001807 | 0.425 | +0.575 | 0.000 |
| Undoped | OOH | O212 | 6.147371 | -0.147371 | +0.591714 | 5.870 | +0.130 | +0.593 |
| Undoped | OOH | O213 | 6.133490 | -0.133490 | +0.256350 | 6.368 | -0.368 | +0.263 |
| Al16 | OH | Co48 | 16.139792 | +0.860208 | +3.204646 | 18.458 | -1.458 | +3.224 |
| Al16 | OH | H221 | 0.671364 | +0.328637 | +0.006066 | 0.427 | +0.573 | +0.001 |
| Al16 | OH | O222 | 6.671766 | -0.671766 | +0.339262 | 6.299 | -0.299 | +0.336 |
| Al16 | O | Co48 | 16.190029 | +0.809970 | +2.877203 | 18.470 | -1.470 | +2.776 |
| Al16 | O | O221 | 6.368453 | -0.368453 | -0.462897 | 5.872 | +0.128 | -0.408 |
| Al16 | OOH | Co48 | 16.150375 | +0.849625 | +3.161831 | 18.379 | -1.379 | +3.146 |
| Al16 | OOH | H221 | 0.711770 | +0.288230 | +0.009329 | 0.421 | +0.579 | +0.001 |
| Al16 | OOH | O222 | 6.254195 | -0.254195 | +0.428481 | 5.917 | +0.083 | +0.427 |
| Al16 | OOH | O223 | 6.218971 | -0.218971 | +0.171329 | 6.189 | -0.189 | +0.187 |

### 5.2 cDFT 基线 *OH -> *O 原子变化

`Delta N = N(*O) - N(*OH)`；`Delta m = m(*O) - m(*OH)`。

| 分区 | 体系 | 原子 | Delta N / e | Delta q / e | Delta m / muB | 机理含义 |
|---|---|---|---:|---:|---:|---|
| Hirshfeld | Undoped | Coact | +0.219 | -0.219 | -0.821 | Co 明显参与还原式电荷补偿并降低自旋 |
| Hirshfeld | Undoped | Oads | -0.464 | +0.465 | -0.070 | O 失电子，但自旋方向保持正 |
| Hirshfeld | Al16 | Coact | +0.012 | -0.012 | -0.448 | Co 净电荷响应几乎被缓冲 |
| Hirshfeld | Al16 | Oads | -0.427 | +0.427 | -0.744 | O 承担强自旋响应，`+0.336 -> -0.408`，发生自旋反转 |
| Mulliken | Undoped | Coact | +0.147192 | -0.147191 | -0.799981 | 与 Hirshfeld 同方向 |
| Mulliken | Undoped | Oads | -0.142383 | +0.142383 | -0.062815 | O 失电子，正自旋保持 |
| Mulliken | Al16 | Coact | +0.050237 | -0.050238 | -0.327443 | Co 响应小于未掺杂 |
| Mulliken | Al16 | Oads | -0.303313 | +0.303313 | -0.802159 | O 自旋反转，`+0.339262 -> -0.462897` |

绘图优先采用 Hirshfeld cDFT 数字，因为它最直接表达“未掺杂 Co 有明显电荷响应，Al16 Co 近乎无净电荷响应”。必须标注为 `cDFT Hirshfeld`，不得写成 Bader。

### 5.3 全部 cDFT 约束罚能

| 状态 | 约束范围 | 方向 | Undoped / eV | Al16 / eV | Al16-Undoped / eV | 状态 |
|---|---|---|---:|---:|---:|---|
| OH | Co-only | N-1 | 4.913867 | 4.889379 | -0.024488 | valid |
| OH | Co-only | N+1 | 4.397178 | 4.454942 | +0.057764 | valid |
| O | Co-only | N-1 | 5.255931 | 5.146837 | -0.109094 | valid |
| O | Co-only | N+1 | 4.822150 | 4.141331 | -0.680819 | valid |
| OOH | Co-only | N-1 | 5.269218 | 5.080396 | -0.188822 | valid |
| OOH | Co-only | N+1 | 4.315024 | 4.165019 | -0.150005 | valid |
| OH | Co+adsorbate | N-1 | 3.102077 | 3.385023 | +0.282946 | valid |
| OH | Co+adsorbate | N+1 | 3.216547 | 3.771411 | +0.554864 | valid |
| O | Co+adsorbate | N-1 | 3.311917 | 3.389370 | +0.077453 | valid |
| O | Co+adsorbate | N+1 | 3.657029 | 3.389767 | -0.267262 | valid |
| OOH | Co+adsorbate | N-1 | 3.240959 | 2.873528 | -0.367431 | valid |
| OOH | Co+adsorbate | N+1 | 2.590033 | 2.697286 | +0.107253 | valid |
| O | Co-only-spin | M-2 | 0.869876 | NA | NA | Al16 rejected: spin branch discontinuity |
| O | Co-only-spin | M+2 | 2.899188 | 4.036604 | +1.137416 | valid |

补充 O 态：Co-only M+2 约束在 Al16 中比未掺杂高 `1.137416 eV`，说明强行增加 Co 自旋在 Al16 中更困难。Al16 M-2 分支不连续，绝不能拟合、插值或绘制为有效点。

### 5.4 cDFT 局域化解释

- Co-only N-1 代价约 `4.89-5.27 eV`。
- Co+adsorbate N-1 代价约 `2.87-3.39 eV`。
- 后者明显更低，支持 Co-O 离域配体空穴，而不是整数 Co-only 氧化。
- Al 对三个中间体不是单调效应：OH N-1 更难 `+0.282946 eV`，O 仅稍难 `+0.077453 eV`，OOH 更容易 `-0.367431 eV`。
- 因此不能把 Al 画成简单统一吸电子掺杂剂。

---

## 6. VASP-Bader 固定几何原子数据

### 6.1 所有机理相关原子

| 体系 | 构型 | 角色/原子 | N_Bader / e | q / e | Basin volume / A3 | m / muB |
|---|---|---|---:|---:|---:|---:|
| Undoped | OH | Coact Co21 | 7.627093 | +1.372907 | 8.910695 | +2.941 |
| Undoped | OH | Coadj Co23 | 7.676855 | +1.323145 | 9.225684 | +2.750 |
| Undoped | OH | H116 | 0.661799 | +0.338201 | 20.364429 | +0.002 |
| Undoped | OH | Obridge O259 | 6.889133 | -0.889133 | 10.496701 | +0.108 |
| Undoped | OH | adjacent-OH O260 | 6.951499 | -0.951499 | 10.889620 | +0.077 |
| Undoped | OH | Oads O348 | 6.618730 | -0.618730 | 17.503887 | +0.159 |
| Undoped | O | Coact Co21 | 7.652966 | +1.347034 | 8.890332 | +2.834 |
| Undoped | O | Coadj Co23 | 7.675405 | +1.324595 | 9.221913 | +2.747 |
| Undoped | O | H116 | 0.659194 | +0.340806 | 20.351860 | +0.002 |
| Undoped | O | Obridge O258 | 6.865569 | -0.865569 | 10.446926 | +0.047 |
| Undoped | O | adjacent-OH O259 | 6.952636 | -0.952636 | 10.896910 | +0.078 |
| Undoped | O | Oads O347 | 6.358038 | -0.358038 | 58.264672 | +0.813 |
| Al16 | OH | Coact Co16 | 7.645947 | +1.354053 | 8.922259 | +3.140 |
| Al16 | OH | Al51 | 0.911539 | +2.088461 | 7.348571 | +0.003 |
| Al16 | OH | H116 | 0.634945 | +0.365055 | 20.234965 | +0.002 |
| Al16 | OH | Obridge O259 | 6.956695 | -0.956695 | 10.671667 | +0.064 |
| Al16 | OH | adjacent-OH O260 | 7.049812 | -1.049812 | 11.425076 | +0.053 |
| Al16 | OH | Oads O348 | 6.650293 | -0.650293 | 17.511680 | +0.328 |
| Al16 | O | Coact Co16 | 7.676377 | +1.323623 | 8.907678 | +3.107 |
| Al16 | O | Al51 | 0.910879 | +2.089121 | 7.341532 | +0.003 |
| Al16 | O | H116 | 0.634935 | +0.365065 | 20.228931 | +0.002 |
| Al16 | O | Obridge O258 | 6.956979 | -0.956979 | 10.644768 | +0.057 |
| Al16 | O | adjacent-OH O259 | 7.050332 | -1.050332 | 11.425328 | +0.053 |
| Al16 | O | Oads O347 | 6.426088 | -0.426088 | 57.085160 | +1.028 |

Oads 在 O 态的 Bader basin volume 大幅增大，是真空/表面 Bader 拓扑改变导致的敏感量，不应在机理图中用球体大小表示，也不应用来推断原子尺寸。

### 6.2 Bader *OH -> *O 变化

| 体系 | 角色 | Delta N / e | Delta q / e | Delta m / muB | Delta volume / A3 |
|---|---|---:|---:|---:|---:|
| Undoped | Coact | +0.025873 | -0.025873 | -0.107 | -0.020363 |
| Undoped | Coadj | -0.001450 | +0.001450 | -0.003 | -0.003771 |
| Undoped | Obridge | -0.023564 | +0.023564 | -0.061 | -0.049775 |
| Undoped | adjacent-OH O | +0.001137 | -0.001137 | +0.001 | +0.007290 |
| Undoped | adjacent-OH H | -0.002605 | +0.002605 | 0.000 | -0.012569 |
| Undoped | Oads | -0.260692 | +0.260692 | +0.654 | +40.760785 |
| Al16 | Coact | +0.030430 | -0.030430 | -0.033 | -0.014581 |
| Al16 | Al | -0.000660 | +0.000660 | 0.000 | -0.007039 |
| Al16 | Obridge | +0.000284 | -0.000284 | -0.007 | -0.026899 |
| Al16 | adjacent-OH O | +0.000520 | -0.000520 | 0.000 | +0.000252 |
| Al16 | adjacent-OH H | -0.000010 | +0.000010 | 0.000 | -0.006034 |
| Al16 | Oads | -0.224205 | +0.224205 | +0.700 | +39.573480 |

核心 Bader 读法：

- 两种体系的 Oads 都是主要失电子位点。
- Al16 使 Oads 净失电子减少 `0.036487 e`。
- 活性 Co Bader 净得电子在两种体系都约 `0.03 e`，Bader 不支持“Al 后 Co 完全无电荷变化”的单独结论。
- Al16 将 Co 磁矩下降从 `-0.107` 缓冲到 `-0.033 muB`，下降幅度减少约 69%。
- Al 自身 `Delta N = -0.000660 e`、`Delta m = 0`，基本不参与局域氧化还原或磁矩变化。
- 未掺杂 Obridge 有 `-0.023564 e` 和 `-0.061 muB` 的响应；Al16 Obridge 仅 `+0.000284 e` 和 `-0.007 muB`，桥联骨架更静止。

### 6.3 裸位点电子替换效应

| 体系 | 原子 | N_Bader | q | m / muB | occupied d center / eV |
|---|---|---:|---:|---:|---:|
| Undoped bare | Coact Co21 | 7.625498 | +1.374502 | 2.984 | -5.03473267 |
| Al16 bare | Coact Co16 | 7.652354 | +1.347646 | 3.130 | -4.95284119 |
| Undoped bare | Coadj Co23 | 7.677983 | +1.322017 | 2.750 | - |
| Al16 bare | Al51 | 0.913443 | +2.086557 | 0.003 | - |

Al16 裸位点活性 Co 比未掺杂多 `0.026856 e`，磁矩高 `0.146 muB`，occupied d center 上移 `0.08189148 eV`。这是初始电子结构差异，不等同于反应过程的 Delta 值。

---

## 7. LOBSTER 逐轨道电子布居变化

以下为 `Delta population = population(*O) - population(*OH)`。轨道轴是 VASP 全局坐标，不是以 Co-O 键为 z 轴的局域坐标；不能直接把 `dz2` 画成轴向 Co-O sigma 轨道，除非先做局域坐标旋转。

### 7.1 Mulliken/Lowdin 逐轨道、逐自旋变化

| 体系 | 原子轨道 | Mulliken up | Mulliken down | Lowdin up | Lowdin down |
|---|---|---:|---:|---:|---:|
| Undoped | Co dxy | -0.030 | +0.050 | -0.030 | +0.050 |
| Undoped | Co dyz | +0.030 | +0.040 | +0.030 | +0.040 |
| Undoped | Co dz2 | 0.000 | -0.130 | 0.000 | -0.130 |
| Undoped | Co dxz | -0.020 | +0.080 | -0.020 | +0.090 |
| Undoped | Co dx2-y2 | +0.010 | +0.050 | +0.010 | +0.050 |
| Undoped | Oads py | +0.020 | -0.410 | +0.030 | -0.400 |
| Undoped | Oads pz | +0.090 | 0.000 | +0.090 | +0.010 |
| Undoped | Oads px | +0.050 | -0.250 | +0.050 | -0.250 |
| Al16 | Co dxy | 0.000 | +0.080 | 0.000 | +0.080 |
| Al16 | Co dyz | 0.000 | +0.030 | 0.000 | +0.030 |
| Al16 | Co dz2 | 0.000 | -0.190 | 0.000 | -0.190 |
| Al16 | Co dxz | 0.000 | +0.100 | 0.000 | +0.100 |
| Al16 | Co dx2-y2 | 0.000 | +0.020 | 0.000 | +0.020 |
| Al16 | Oads py | +0.050 | -0.460 | +0.060 | -0.450 |
| Al16 | Oads pz | +0.150 | -0.020 | +0.150 | -0.020 |
| Al16 | Oads px | +0.020 | -0.200 | +0.020 | -0.200 |

### 7.2 轨道布居求和

| 体系 | 子空间 | Delta N_up | Delta N_down | Delta N_total | Delta spin = up-down |
|---|---|---:|---:|---:|---:|
| Undoped | Co 3d Mulliken | -0.010 | +0.090 | +0.080 | -0.100 |
| Al16 | Co 3d Mulliken | 0.000 | +0.040 | +0.040 | -0.040 |
| Undoped | Oads 2p Mulliken | +0.160 | -0.660 | -0.500 | +0.820 |
| Al16 | Oads 2p Mulliken | +0.220 | -0.680 | -0.460 | +0.900 |

这组数据对画图非常重要：

- Oads 的少数自旋 2p 电子显著减少，且多数自旋 2p 占据增加。
- Oads 总失电子是少数自旋 O 中心氧化的结果。
- Co 3d 净电子变化小，是多个轨道得失相互抵消的结果；不能用一个单独 d 轨道解释全部过程。
- Al16 中 Co 3d 的多数自旋布居变化接近 0，但少数自旋内部仍有 `dz2 -> dxz/dxy` 等重新分配。
- COHP 所说的“多数自旋差异”是成键能响应，不等同于某一多数自旋轨道净失去一个电子。

---

## 8. 轨道分辨 PDOS 变化

积分窗口为 occupied `-8 to 0 eV`。`Delta weight` 和 `Delta center` 均为 `*O - *OH`。

| 体系 | 轨道 | 自旋 | Delta occupied weight | Delta center / eV |
|---|---|---|---:|---:|
| Undoped | Co dxy | up | -0.038998 | +0.229424 |
| Undoped | Co dxy | down | +0.042613 | -0.079612 |
| Undoped | Co dyz | up | +0.062405 | +0.340598 |
| Undoped | Co dyz | down | +0.035807 | -0.039697 |
| Undoped | Co dz2 | up | +0.002919 | -0.148599 |
| Undoped | Co dz2 | down | -0.127423 | +0.062103 |
| Undoped | Co dxz | up | -0.028400 | +0.183544 |
| Undoped | Co dxz | down | +0.073029 | -0.230960 |
| Undoped | Co dx2-y2 | up | +0.010095 | +0.237998 |
| Undoped | Co dx2-y2 | down | +0.047889 | -0.082196 |
| Undoped | Oads py | up | +0.106876 | -0.527160 |
| Undoped | Oads py | down | -0.235821 | -0.443280 |
| Undoped | Oads pz | up | +0.067144 | +1.433127 |
| Undoped | Oads pz | down | -0.064019 | +1.710416 |
| Undoped | Oads px | up | +0.216708 | -0.520918 |
| Undoped | Oads px | down | -0.082590 | -0.908248 |
| Al16 | Co dxy | up | +0.058447 | +0.346449 |
| Al16 | Co dxy | down | +0.077466 | +0.152334 |
| Al16 | Co dyz | up | -0.003648 | +0.159113 |
| Al16 | Co dyz | down | +0.026035 | -0.001171 |
| Al16 | Co dz2 | up | -0.006339 | -0.098866 |
| Al16 | Co dz2 | down | -0.188984 | +0.145503 |
| Al16 | Co dxz | up | -0.004990 | +0.431142 |
| Al16 | Co dxz | down | +0.086115 | +0.049136 |
| Al16 | Co dx2-y2 | up | +0.008483 | +0.341995 |
| Al16 | Co dx2-y2 | down | +0.020905 | +0.043040 |
| Al16 | Oads py | up | +0.090317 | -0.259589 |
| Al16 | Oads py | down | -0.268585 | -0.156719 |
| Al16 | Oads pz | up | +0.119142 | +1.701306 |
| Al16 | Oads pz | down | -0.121024 | +2.106724 |
| Al16 | Oads px | up | +0.028860 | -0.724220 |
| Al16 | Oads px | down | -0.053413 | -0.326265 |

PDOS 权重受投影球和能窗影响，只用于轨道趋势；净电荷优先引用 Bader/cDFT，价键强度优先引用 COHP。

---

## 9. d 带中心

### 9.1 活性 Co 3d

| 体系 | 构型 | occupied center -8..0 / eV | extended center -8..+4 / eV | up occupied / eV | down occupied / eV |
|---|---|---:|---:|---:|---:|
| Undoped | OH | -5.107102 | -2.894794 | -5.877889 | -3.272336 |
| Undoped | O | -5.000525 | -2.873697 | -5.709457 | -3.369260 |
| Al16 | OH | -4.874378 | -2.744211 | -5.555075 | -3.190037 |
| Al16 | O | -4.699149 | -2.602819 | -5.322797 | -3.156407 |

*OH -> *O 活性 Co occupied d-center 上移：

- Undoped：`+0.106577 eV`。
- Al16：`+0.175229 eV`。

### 9.2 整个 Co 框架平均 d-center

| 体系 | 构型 | occupied / eV | extended / eV |
|---|---|---:|---:|
| Undoped | OH | -3.278872 | -2.325196 |
| Undoped | O | -3.280507 | -2.305221 |
| Al16 | OH | -3.604639 | -2.328211 |
| Al16 | O | -3.616496 | -2.322928 |

Al 使局域活性 Co d-center 相对升高，但使框架 occupied d-center 更低。局域和整体平均不能混用。

---

## 10. LOBSTER/COHP 全部相关价键

### 10.1 原始 ICOHP

| 体系 | 构型 | 价键 | 距离 / A | ICOHP spin1 / eV | ICOHP spin2 / eV | total / eV |
|---|---|---|---:|---:|---:|---:|
| Undoped | OH | Coact-Oads | 1.87588 | -0.49618 | -1.43149 | -1.92767 |
| Undoped | OH | Coadj-OH | 2.04312 | -0.51714 | -0.86249 | -1.37963 |
| Undoped | OH | O-H | 0.97545 | -3.86344 | -3.88993 | -7.75337 |
| Undoped | OH | Coact-Obridge | 2.06996 | -0.50467 | -0.85410 | -1.35877 |
| Undoped | OH | Coadj-Obridge | 2.11233 | -0.43606 | -0.73025 | -1.16631 |
| Undoped | O | Coact-Oads | 1.74323 | -1.05645 | -2.33612 | -3.39257 |
| Undoped | O | Coadj-OH | 2.04312 | -0.52013 | -0.86941 | -1.38954 |
| Undoped | O | O-H | 0.97545 | -3.87521 | -3.90404 | -7.77925 |
| Undoped | O | Coact-Obridge | 2.06996 | -0.61525 | -0.81379 | -1.42904 |
| Undoped | O | Coadj-Obridge | 2.11233 | -0.44612 | -0.72457 | -1.17069 |
| Al16 | OH | Coact-Oads | 1.87588 | -0.45504 | -1.47507 | -1.93011 |
| Al16 | OH | Al-OH | 2.04312 | -1.97062 | -1.99407 | -3.96469 |
| Al16 | OH | O-H | 0.97545 | -3.87336 | -3.90736 | -7.78072 |
| Al16 | OH | Coact-Obridge | 2.06996 | -0.46155 | -0.75311 | -1.21466 |
| Al16 | OH | Al-Obridge | 2.11233 | -1.78694 | -1.80194 | -3.58888 |
| Al16 | O | Coact-Oads | 1.74323 | -0.66391 | -2.37854 | -3.04245 |
| Al16 | O | Al-OH | 2.04312 | -1.97659 | -1.99903 | -3.97562 |
| Al16 | O | O-H | 0.97545 | -3.87553 | -3.90866 | -7.78419 |
| Al16 | O | Coact-Obridge | 2.06996 | -0.45384 | -0.72600 | -1.17984 |
| Al16 | O | Al-Obridge | 2.11233 | -1.79013 | -1.80602 | -3.59615 |

所有正式 LOBSTER spilling 为 spin1 `0.92-0.94%`、spin2 `1.24-1.27%`，小于 2%，结果有效。

### 10.2 *OH -> *O 价键变化

| 体系 | 价键 | Delta ICOHP spin1 | Delta ICOHP spin2 | Delta ICOHP total | 解释 |
|---|---|---:|---:|---:|---|
| Undoped | Coact-Oads | -0.56027 | -0.90463 | -1.46490 | 强烈增强 |
| Al16 | Coact-Oads | -0.20887 | -0.90347 | -1.11234 | 总增强较小，差异来自 spin1 |
| Undoped | Coact-Obridge | -0.11058 | +0.04031 | -0.07027 | 小幅增强 |
| Al16 | Coact-Obridge | +0.00771 | +0.02711 | +0.03482 | 小幅减弱 |
| Undoped | 邻位金属-OH | -0.00299 | -0.00692 | -0.00991 | 几乎不变 |
| Al16 | 邻位金属-OH | -0.00597 | -0.00496 | -0.01093 | 几乎不变 |
| Undoped | O-H | -0.01177 | -0.01411 | -0.02588 | 邻位 OH 保持 |
| Al16 | O-H | -0.00217 | -0.00130 | -0.00347 | 邻位 OH 保持 |
| Undoped | 邻位金属-Obridge | -0.01006 | +0.00568 | -0.00438 | 几乎不变 |
| Al16 | 邻位金属-Obridge | -0.00319 | -0.00408 | -0.00727 | 几乎不变 |

最关键的跨材料差值：Coact-Oads 的成键增强在 Al16 中少 `0.35256 eV`；其中 spin1 差 `0.35140 eV`，spin2 仅差 `0.00116 eV`。因此 Al 的主要影响是多数自旋价键重杂化，而不是少数自旋 Co-O 成键通道。

---

## 11. 反应诱导电荷/自旋密度

### 11.1 Al16 同几何自洽差分，已完成

定义：`rho(*O@OHgeom) - rho(*OH@OHgeom)`。

- 全体系积分电荷：`-0.999999997 e`。
- 全体系积分磁化：`+1.239364997 muB`。
- 电荷密度范围：`-1.635038 to +0.893261 e A^-3`。
- 磁化密度范围：`-0.906128 to +1.761299 muB A^-3`。

### 11.2 未掺杂同几何自洽差分，已完成

- 原作业 `111338_0` 因 ALGO=Fast 在 RMM47 持续振荡而取消；其输出不用于最终分析。
- 恢复作业 `111443` 使用 ALGO=Normal 和保守混合，于 2026-09-01 在 DAV47 达到 `dE = -3.5920e-5 eV < EDIFF = 1e-4 eV`，调度器状态 `COMPLETED`、退出码 `0:0`。
- 固定几何：`NSW=0`、`IBRION=-1`；最终 CHGCAR、CONTCAR 和 vasprun.xml 均非空。
- 全体系积分电荷：`-1.000000011 e`。
- 全体系积分磁化：`+3.287869087 muB`。
- 电荷密度范围：`-1.678282 to +0.944033 e A^-3`。
- 磁化密度范围：`-2.197942 to +2.140786 muB A^-3`。

### 11.3 正式同几何差分对比

| 体系 | integral Delta charge / e | integral Delta m / muB |
|---|---:|---:|
| Undoped self-consistent | -1.000000011 | +3.287869087 |
| Al16 self-consistent | -0.999999997 | +1.239364997 |

- 两个电荷差分都严格对应移去一个电子，因此可直接比较。
- `Al16 - undoped` 的积分自旋响应差为 `-2.048504090 muB`，即 Al16 的全体系自旋响应降低约 `62.3%`。
- 正式热图显示，未掺杂体系在 Oads 和 Co(act) 周围具有更强、空间上更连续的自旋重排；Al16 中 Co(act) 附近的净自旋响应明显减弱，而 Oads 仍承担主要自旋极化。
- 该空间分布与 cDFT 的“活性 Co 自旋/电荷缓冲、O 中心响应”一致，但积分磁化是全体系量，不能直接等同于单个原子的 Bader 磁矩。

### 11.4 启动密度代理，仅用于早期可视化

代理定义：`rho(formal *O) - rho(formal *OH)`，包含结构变化，不是同几何自洽差分。

| 体系 | integral Delta charge / e | integral Delta m / muB |
|---|---:|---:|
| Undoped proxy | -1.000000011 | +2.315765617 |
| Al16 proxy | -0.999999998 | +1.346926337 |

代理显示 Al16 总磁化响应比未掺杂低约 42%，与自旋缓冲趋势一致；不能用代理等值面作为最终定量证据。

---

## 12. 质子转移/Al-OH 中继筛选

该计算检验相邻 Al-bound OH 是否直接接受 Co-OH 的质子。重原子固定，属于路径筛选，不是 NEB，不是自由能势垒。

### 12.1 中性固定路径全部 7 个图像

| 图像 | Al16 H-acceptor / A | Al16 relative E / eV | Undoped H-acceptor / A | Undoped relative E / eV |
|---:|---:|---:|---:|---:|
| 0 initial | 3.492257 | 0.000000 | 1.813332 | 0.000000 |
| 1 rotated | 1.580988 | 1.631059 | 1.725284 | 0.190815 |
| 2 transfer 0.20 | 1.461222 | 1.844544 | 1.580267 | 0.399835 |
| 3 transfer 0.40 | 1.341457 | 2.231805 | 1.435250 | 0.735697 |
| 4 transfer 0.60 | 1.221691 | 2.610560 | 1.290233 | 0.892610 |
| 5 transfer 0.80 | 1.101925 | 2.946224 | 1.145216 | 0.789425 |
| 6 transfer 1.00 | 0.982160 | 3.362339 | 1.000198 | 0.708609 |

### 12.2 N-1 条件化代表图像

| 体系 | 图像 | neutral relative / eV | N-1 penalty / eV | N-1-conditioned relative / eV | Co spin | donor O spin |
|---|---:|---:|---:|---:|---:|---:|
| Al16 | 0 | 0.000000 | 3.415750 | 0.000000 | 3.561 | 0.830 |
| Al16 | 4 | 2.610560 | 3.309289 | 2.504099 | 3.435 | 1.114 |
| Al16 | 6 | 3.362339 | 3.361551 | 3.308140 | 3.415 | 1.286 |
| Undoped | 0 | 0.000000 | 3.102247 | 0.000000 | 3.536 | 1.082 |
| Undoped | 4 | 0.892610 | 3.677509 | 1.467872 | 3.541 | 1.362 |
| Undoped | 6 | 0.708609 | 3.653094 | 1.259456 | 3.542 | 1.689 |

结论：当前 Al-bound OH 几何不是有利的直接质子受体。Al16 初始 OH 指向错误，需要高代价旋转；氧化也没有反转该结论。机理图不得画成“质子转移到 Al-OH 导致活性提高”。其他溶剂化水网络或不同 Al 排布仍未排除。

---

## 13. 数据之间的一致性与表面矛盾

### 13.1 cDFT Co 电荷缓冲 vs Bader Co 约 0.03 e

- cDFT Hirshfeld：Coact `Delta N` 从未掺杂 `+0.219 e` 降到 Al16 `+0.012 e`。
- Bader：Coact `Delta N` 为未掺杂 `+0.025873 e`、Al16 `+0.030430 e`。
- 两者不矛盾：cDFT 比较局域约束下 Co/Co-O 对加减电子的响应；Bader 比较不同最终基态的拓扑盆净电荷。
- 绘图时若强调“Al 后 Co 净电荷响应接近零”，必须标注 `cDFT Hirshfeld`。
- 若使用 Bader，则只能说“两体系 Co 的最终净 Bader 电荷变化都小，Al 主要缓冲 Co 磁矩而非 Bader 净电荷”。

### 13.2 O 少数自旋失电子 vs COHP 多数自旋差异

- O 2p 轨道布居显示少数自旋大量减少，因此净失电子是少数自旋 O 中心氧化。
- COHP 显示 Al 与未掺杂的价键增强差异发生在多数自旋。
- 这是两个同时发生但不同的过程：
  1. 少数自旋电子从 Oads 2p 移向外电路。
  2. 剩余电子发生多数自旋 Co-O 成键重杂化；该补偿通道被 Al 抑制。
- 机理图必须用两种不同箭头，不得把“多数自旋成键重排”画成“多数自旋电子被直接移走”。

### 13.3 单轨道解释的限制

- 全局坐标轨道布居中，Co dz2-down 减少，同时 dxz/dxy-down 等增加，多个轨道相互补偿。
- Co 3d 净变化只有未掺杂 `+0.08 e`、Al16 `+0.04 e`。
- 未建立局域 Co-O 坐标系前，不能声称唯一的 `dz2`、`dxz` 或 `eg` 轨道控制机理。
- 论文图可用 `t2g-like` 和 `eg-like` 定性分组，并注明 distorted octahedral / qualitative。

### 13.4 Al-O 骨架的角色

- Al 的 Bader 电荷和磁矩在 OH->O 中几乎不变。
- Al-OH、Al-Obridge ICOHP 变化均约 `0.01 eV` 或更小。
- Al-O 骨架不是主要氧化还原中心，也不是当前几何下的有利质子中继。
- Al 的合理角色是改变局域静电场、配体场和 O 介导的磁性交换边界条件。

---

## 14. 推荐给绘图 AI 的逐步机理叙事

### Step A：初始局域结构

- 左：`*OH-Coact-Obridge-Coadj`，邻位 Co 有磁性 3d 态，可通过 Obridge 形成 d-p-d 交换。
- 右：`*OH-Coact-Obridge-Al`，Al 磁矩约 `0.003 muB`，近费米能级没有磁性 3d 态。
- OH 构型的 Coact-Oads 距离均为 `1.87588 A`；O 构型均缩短为 `1.74323 A`。

### Step B：PCET 去质子化

- 反应：`*OH -> *O + H+ + e-`。
- 不画质子转移到 Al-OH；画 H+ 和 e- 离开局域活性位。
- Oads 是主要净失电子位点。

### Step C：O 中心少数自旋氧化

- 用蓝色向下自旋箭头表示少数自旋电子从 Oads 2p 移出。
- 两种体系均有该过程。
- 轨道求和：Undoped Oads `Delta N_down = -0.660 e`；Al16 `-0.680 e`。
- 同时 Oads 多数自旋占据增加：Undoped `+0.160 e`；Al16 `+0.220 e`。

### Step D：多数自旋 Co-O 重杂化

- 用橙色多数自旋箭头表示 Oads 2p-Coact 3d-Obridge 2p-邻位金属的成键重排。
- 未掺杂为连续较强的 Co-O-Co 通道。
- Al16 在 Al 前终止/变细，因为没有邻位磁性 Co 3d 态。
- COHP 量化：多数自旋 `Delta(-ICOHP)` 从 `0.560` 降至 `0.209 eV`；少数自旋 `0.905` 与 `0.903 eV` 基本相同。

### Step E：Co 自旋缓冲和 O 中心响应

- Bader/OUTCAR：Coact `Delta m` 从 `-0.107` 缓冲到 `-0.033 muB`。
- cDFT Hirshfeld：Coact `Delta N` 从 `+0.219` 缓冲到 `+0.012 e`。
- cDFT Oads：Al16 从 `+0.336` 变成 `-0.408 muB`，显示 O 自旋反转。
- Bader Oads：磁矩增加未掺杂 `+0.654`、Al16 `+0.700 muB`。

### Step F：价键结果

- Coact-Oads 均明显增强，但 Al16 增强幅度少 `0.35256 eV`。
- 未掺杂 Coact-Obridge 小幅增强 `-0.07027 eV`；Al16 小幅减弱 `+0.03482 eV`。
- 邻位 Co/Al-OH、Co/Al-Obridge 和 O-H 基本不变。
- 不把较小 Co-O 增强直接等同于更低热力学电位；它证明的是不同的电子重组路径。

### Step G：与实验的连接

- 实验：Al 后 *OH 到 *O 更容易。
- 已完成计算支持：关键步骤一致、Co 自旋重组减少、O 中心响应增强、历史和初步电位趋势降低。
- 尚待最终确认：覆盖度依赖脱质子电位序列。

---

## 15. 绘图 AI 的硬性规范

### 15.1 必须画出的元素

1. 两个并列框架：`(i) *OH-Co-O-Co` 与 `(ii) *OH-Co-O-Al`。
2. 传统反应：`*OH -> *O + H+ + e-`。
3. 蓝色少数自旋 O 中心失电子箭头，指向 `e- to electrode`。
4. 橙色多数自旋 Co-O 重杂化路径：未掺杂连续且较强，Al16 在 Al 前减弱/中断。
5. 少数自旋 Co-O 成键通道在两侧画成近似相同。
6. distorted-octahedral `t2g-like` 三重和 `eg-like` 二重能级；上下箭头仅作定性自旋占据。
7. Al 画成非磁性，不画 Al 3d 占据。
8. 可选关键数值：
   - cDFT Hirshfeld `Delta N(Coact): +0.219 vs +0.012 e`。
   - cDFT Hirshfeld `Delta m(Oads): -0.070 vs -0.744 muB`。
   - Bader/OUTCAR `Delta m(Coact): -0.107 vs -0.033 muB`。
   - COHP `Delta(-ICOHP) spin1/spin2: 0.560/0.905 vs 0.209/0.903 eV`。

### 15.2 禁止画出的内容

- 不画 O-O 形成；本图只讨论 *OH 到 *O。
- 不画质子转移到 Al-OH，因为当前路径筛选不支持。
- 不画确定的最终 Al 脱质子电位；覆盖度序列未完成。
- 不把 cDFT、Bader 和 LOBSTER 数字放在同一个未标注的 `charge transfer` 箭头上。
- 不把多数自旋 COHP 变化误画成多数自旋电子从 O 被移走。
- 不指定唯一 `dz2` 或 `dxz` 控制轨道。
- 不画 Al 为磁性中心，不给 Al 画占据 3d 能级。
- 不使用海报/PPT式大标题、彩色横幅、数据柱状图或大段结论框。

### 15.3 推荐论文图版式

- 纯白背景，细黑线，低饱和 Co 蓝、O 红、Al 洋红。
- 左右两个并列机理小图，不使用外框或大色块。
- 上部为局域结构和电子箭头，下部为简化能级图。
- 数字采用小型文字注释，不使用表格或条形图。
- 橙色上箭头：`spin 1, majority at Coact`。
- 蓝色下箭头：`spin 2, minority at Coact`。
- 图注中明确：`ligand-field levels are qualitative; numerical charges depend on partitioning method`。

---

## 16. 可直接提供给 ChatGPT Image 2 的短版事实摘要

```text
Draw a concise journal mechanism panel comparing *OH-Coact-Obridge-Coadj and *OH-Coact-Obridge-Al during *OH -> *O + H+ + e-. Net oxidation is O-centered minority-spin electron removal in both systems: LOBSTER Oads 2p Delta N_down is -0.660 e undoped and -0.680 e Al16, while Delta N_up is +0.160 and +0.220 e. The Al effect is not a change in the removed spin; it selectively buffers majority-spin Co-O bond rehybridization. Spin-resolved Delta(-ICOHP) for Coact-Oads is spin1/spin2 = 0.560/0.905 eV undoped and 0.209/0.903 eV Al16. Bader/OUTCAR Delta m(Coact) is -0.107 versus -0.033 muB. cDFT Hirshfeld Delta N(Coact) is +0.219 versus +0.012 e, and Delta m(Oads) is -0.070 versus -0.744 muB, with Oads spin reversal only in Al16. Draw Al as nonmagnetic and without near-EF magnetic 3d states. Use qualitative distorted-octahedral t2g-like and eg-like levels with up/down arrows, but do not assign an exact individual d orbital. Do not draw O-O formation, proton transfer to Al-OH, a final deprotonation potential, or an exact Co oxidation state.
```

---

## 17. 原始本地数据文件

- `cdft_undoped_vs_al16_complete_20260818.tsv`
- `cdft_oh_to_o_charge_spin_20260820.tsv`
- `cdft_baseline_population_summary.tsv`
- `undoped_cdft_baseline_population_summary.tsv`
- `cohp_oh_to_o_academic_summary_20260824.tsv`
- `lobster_orbital_population_oh_to_o_20260826.tsv`
- `orbital_resolved_pdos_oh_to_o_20260826.tsv`
- `d_band_center_oh_o_20260824.tsv`
- `d_band_center_framework_oh_o_20260824.tsv`
- `deprotonation_potential_preliminary_20260824.tsv`
- `proton_relay_fixed_path_20260817.tsv`
- `proton_relay_pcet_nm1_profile_20260818.tsv`
- `strict_site03_vasp_298p15K_che_summary.tsv`
- `strict_site03_vasp_298p15K_staircase.tsv`
- `cohp_oh_o_inputs_20260824/*/ICOHPLIST.lobster`

该文档中的四组正式 Bader ACF.dat 数值和 OUTCAR 局域磁矩于 2026-08-31 从 `/home/ftfan/ncw` 下已验证结果目录只读提取。
