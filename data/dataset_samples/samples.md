# 中文关系抽取数据集：各10条真实标注样例

共5个数据集、50条三元组。DuIE、CMeIE、TPSCRE各取前10条有标注记录的第一条关系；SanWen取10个不同测试文档中的第一条关系；地质灾害取第一个分组中的前10个三元组。

这是标注结构抽样核查，不是对标注事实、完整性或全数据集质量的审核。保持原始实体文字、关系标签和方向，不纠正可疑标注。

CMeIE此次使用Hugging Face的第三方镜像；SanWen使用作者原始仓库，并非此前找到的OpenDataLab镜像。SanWen只显示有关实体附近的原文节选。地质灾害两个JSON没有每条三元组对应的原文，该文件另有JSON格式问题；本报告只解析首个完整JSON数组，未修复源文件。

## DuIE

来源：[数据页面](https://www.kaggle.com/datasets/mushansanren/duiedata)

| 编号 | 主体 | 关系 | 客体 |
|---|---|---|---|
| 1 | 何以笙箫默 | 作者 | 顾漫 |
| 2 | 摩尔多瓦 | 首都 | 基希讷乌 |
| 3 | 喜剧之王 | 编剧 | 周星驰 |
| 4 | 天城公主 | 丈夫 | 国峻 |
| 5 | 情人节 | 票房 | 4亿 |
| 6 | 父老乡亲 | 歌手 | 范琳琳 |
| 7 | 温氏股份 | 董事长 | 温鹏程 |
| 8 | 宋竹范 | 毕业院校 | 佳木斯医学院 |
| 9 | 与狼共舞2 | 主演 | 赵荀 |
| 10 | 科库雷克 | 国籍 | 捷克 |

### 样例1

文件：`DUIE/duie_dev.json`；记录：`1`

原文：

《步步惊心》改编自著名作家桐华的同名清穿小说《甄嬛传》改编自流潋紫所著的同名小说电视剧《何以笙箫默》改编自顾漫同名小说《花千骨》改编自fresh果果同名小说《裸婚时代》是月影兰析创作的一部情感小说《琅琊榜》是根据海宴同名网络小说改编电视剧《宫锁心玉》，又名《宫》《雪豹》，该剧改编自网络小说《特战先驱》《我是特种兵》由红遍网络的小说《最后一颗子弹留给我》改编电视剧《来不及说我爱你》改编自匪我思存同名小说《来不及说我爱你》

原始关系标注：

```json
{
  "predicate": "作者",
  "object_type": {
    "@value": "人物"
  },
  "subject_type": "图书作品",
  "object": {
    "@value": "顾漫"
  },
  "subject": "何以笙箫默"
}
```

### 样例2

文件：`DUIE/duie_dev.json`；记录：`2`

原文：

摩尔多瓦共和国（摩尔多瓦语：Republica Moldova，英语：Republic of Moldova），简称摩尔多瓦，是位于东南欧的内陆国，与罗马尼亚和乌克兰接壤，首都基希讷乌

原始关系标注：

```json
{
  "predicate": "首都",
  "object_type": {
    "@value": "城市"
  },
  "subject_type": "国家",
  "object": {
    "@value": "基希讷乌"
  },
  "subject": "摩尔多瓦"
}
```

### 样例3

文件：`DUIE/duie_dev.json`；记录：`3`

原文：

2月19日，96岁的资深演员侯焕玲离世，候婆婆一生未嫁，但一直热爱电影，她曾在《回魂夜》和《喜剧之王》等电影饰演婆婆一角，而临终前候婆婆一直说，自己好喜欢电影，好喜欢周星驰

原始关系标注：

```json
{
  "predicate": "编剧",
  "object_type": {
    "@value": "人物"
  },
  "subject_type": "影视作品",
  "object": {
    "@value": "周星驰"
  },
  "subject": "喜剧之王"
}
```

### 样例4

文件：`DUIE/duie_dev.json`；记录：`4`

原文：

这件婚事原本与陈国峻无关，但陈国峻却“欲求配而无由，夜间乃潜入天城公主所居通之

原始关系标注：

```json
{
  "predicate": "丈夫",
  "object_type": {
    "@value": "人物"
  },
  "subject_type": "人物",
  "object": {
    "@value": "国峻"
  },
  "subject": "天城公主"
}
```

### 样例5

文件：`DUIE/duie_dev.json`；记录：`5`

原文：

情人节大盘约在4亿特工票房1.32拉拉蓝1.05其他没所谓了@0216幻影9527 @朦胧之于暖春 @Jqpiero @娶个明星这么难 @星爷最低调

原始关系标注：

```json
{
  "predicate": "票房",
  "object_type": {
    "@value": "Number"
  },
  "subject_type": "影视作品",
  "object": {
    "@value": "4亿"
  },
  "subject": "情人节"
}
```

### 样例6

文件：`DUIE/duie_dev.json`；记录：`6`

原文：

《父老乡亲》是由是由由中国人民解放军海政文工团创作的军旅歌曲，石顺义作词，王锡仁作曲，范琳琳演唱

原始关系标注：

```json
{
  "predicate": "歌手",
  "object_type": {
    "@value": "人物"
  },
  "subject_type": "歌曲",
  "object": {
    "@value": "范琳琳"
  },
  "subject": "父老乡亲"
}
```

### 样例7

文件：`DUIE/duie_dev.json`；记录：`7`

原文：

2019年2月25日和26日，温氏股份实控人之一、前任董事长温鹏程之妻伍翠珍分别减持公司股票608万股和256万股，成交均价分别为30.78元/股和30.02元/股，共计套现约2.64亿元

原始关系标注：

```json
{
  "predicate": "董事长",
  "object_type": {
    "@value": "人物"
  },
  "subject_type": "企业",
  "object": {
    "@value": "温鹏程"
  },
  "subject": "温氏股份"
}
```

### 样例8

文件：`DUIE/duie_dev.json`；记录：`8`

原文：

宋竹范，口腔医生，女，宋竹范主任医师毕业于佳木斯医学院，在国内三甲医院从事口腔科临床工作三十余年，有丰富的口腔科临床工作经验，熟练掌握口腔内科、口腔外科、儿童口腔科各种常见病及多发病的诊治，以及多项口腔矫形技术

原始关系标注：

```json
{
  "predicate": "毕业院校",
  "object_type": {
    "@value": "学校"
  },
  "subject_type": "人物",
  "object": {
    "@value": "佳木斯医学院"
  },
  "subject": "宋竹范"
}
```

### 样例9

文件：`DUIE/duie_dev.json`；记录：`9`

原文：

由江苏艺星影视文化传播有限公司投资，演员赵荀、傅程鹏、程愫、侯梦莎、任柯诺、安雅萍、杨舒、张进、杨山等主演的大型谍战题材电视剧《与狼共舞2》正在江苏卫视

原始关系标注：

```json
{
  "predicate": "主演",
  "object_type": {
    "@value": "人物"
  },
  "subject_type": "影视作品",
  "object": {
    "@value": "赵荀"
  },
  "subject": "与狼共舞2"
}
```

### 样例10

文件：`DUIE/duie_dev.json`；记录：`10`

原文：

科库雷克(RadovanKocurek),出生于1986年2月12日，捷克国籍，身高179厘米，体重72公斤，场上位置前锋，现在效力于贾洛内足球俱乐部

原始关系标注：

```json
{
  "predicate": "国籍",
  "object_type": {
    "@value": "国家"
  },
  "subject_type": "人物",
  "object": {
    "@value": "捷克"
  },
  "subject": "科库雷克"
}
```

## TPSCRE

来源：[数据页面](https://www.scidb.cn/en/detail?dataSetId=e9c545b78cce49dc81436a015430ac4c)

| 编号 | 主体 | 关系 | 客体 |
|---|---|---|---|
| 1 | 药物 | 包含 | 苍术 |
| 2 | 中药组合物 | 包含 | 黄连 |
| 3 | 所述药物 | 包含 | 黄芪 |
| 4 | 中药组合物 | 包含 | 淫羊藿 |
| 5 | 中成药制剂 | 包含 | 熟地 |
| 6 | 中药 | 包含 | 白芍 |
| 7 | 中药制剂 | 包含 | 黄芪 |
| 8 | 中药制剂 | 包含 | 红曲老醋 |
| 9 | 药物 | 包含 | 白芍 |
| 10 | 本发明 | 功效 | 健脾祛湿 |

### 样例1

文件：`中药专利数据集/test.json`；记录：`1`

原文：

本发明属于中药制剂领域，目的是根据中医治疗痤疮的认识机理而提供的一种治疗痤疮的丸剂药物，所述药物的各个组分及其质量份比如下：赤芍50～100g、薏苡仁150～600g、僵蚕50～100g、牡丹皮80～180g、栀子100～250g、金银花100～260g、白鲜皮50～100g、紫草50～100g、茯苓150～300g、马齿苋90～160g、黄芩30～100g、蒲公英100～350g、桑叶50～100g、苍术（炒）30～100g、白芷30～120g、百部30～100g、土茯苓150～650g、青皮30～120g、连翘60～160g，本发明提供的药物是一个很好的中药组方。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    46,
    47
  ],
  "subject_type": "中药制剂",
  "object": [
    203,
    204
  ],
  "object_type": "成分"
}
```

### 样例2

文件：`中药专利数据集/test.json`；记录：`2`

原文：

本发明属于中药制剂领域，目的是根据中医对痰淤藴热所致小儿智能低下的认识机理而提供的一种治疗痰淤藴热所致小儿智能低下的中药组合物，所述中药组合物的各个组分及其质量份比如下：远志50～160g、人参30～160g、青皮30～120g、石菖蒲50～120g、黄芩50～160g、龟甲90～260g、黄连15～35g、大黄50～200g、当归80～160g、白芍100～220g、川芎50～120g、五味子30～100g、丹参80～160g、葛根80～160g；本发明提供的药物是一个标本兼治的中药组方。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    66,
    70
  ],
  "subject_type": "中药制剂",
  "object": [
    146,
    147
  ],
  "object_type": "成分"
}
```

### 样例3

文件：`中药专利数据集/test.json`；记录：`3`

原文：

本发明属于中药制剂领域，目的是根据中医治疗头痛的认识机理而提供一种用于治疗头痛的丸剂药物，所述药物的各个组分及其质量份比如下：黄芪90～380g、川芎50～120g、红花30～120g、丹参80～180g、白芍100～260g、决明子90～180g，本发明提供的药物是一个很好的中药组方。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    45,
    48
  ],
  "subject_type": "中药制剂",
  "object": [
    63,
    64
  ],
  "object_type": "成分"
}
```

### 样例4

文件：`中药专利数据集/test.json`；记录：`4`

原文：

本发明属于中药制剂领域，目的是根据中医对类风湿性关节炎的认识机理而提供的一种用于治疗类风湿关节炎的中药组合物，所述中药组合物的各个组分及其质量份比如下：黄芪150～360g、桂枝30～120g、白芍50～150g、清风藤100～160g、知母60～150g、麻黄15～100g、姜黄50～160g、生地黄100～160g、丹参80～160g、白芷30～100g、南蛇藤150～260g、淫羊藿50～160g、鸡血藤150～260g、泽泻60～120g；本发明提供的药物是一个标本兼治的中药组方。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    57,
    61
  ],
  "subject_type": "中药制剂",
  "object": [
    193,
    195
  ],
  "object_type": "成分"
}
```

### 样例5

文件：`中药专利数据集/test.json`；记录：`5`

原文：

本发明提供了一种治疗慢性阻塞性肺疾病的中成药制剂，包括以下重量配比的中药原料：黄芪30-50、人参6-12、丹参15-30、熟地20-50、麦冬10-20和半夏6-10。该中成药制剂的制备方法是按配方取各中药原料共同粉碎加工成超过100目以上的细粉，混合均匀，臭氧灭菌20分钟，制成胶囊剂型，或加入蜂蜜调匀制成药丸剂型。本发明为纯中药制剂，诸药相伍，可达到益肺脾心肾、祛除痰瘀、标本兼治的目的，治疗慢性阻塞性肺疾病疗效显著，生产方法简单，成本低廉，无明显毒副作用，患者容易接受。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    19,
    23
  ],
  "subject_type": "中药制剂",
  "object": [
    62,
    63
  ],
  "object_type": "成分"
}
```

### 样例6

文件：`中药专利数据集/test.json`；记录：`6`

原文：

本发明涉及医药保健领域，具体为一种治疗肾病的药物及其制备方法和应用。所述治疗肾病的中药包括：茯苓5~~25克，白术10~~30克，附子5~~25克，白芍10~~30克，西洋参5~~15克，黄连5~~20克，苏叶10~~25克，猪苓5~~30克，泽泻5~~25克，鹿茸3~~9克，冬虫夏草3~~12克，山药10~~30克，山茱萸10~~35克，杜仲10~~25克，金樱子10~~30克，黄芪5~~25克，鲜崩大碗50~~200克。本发明提供一种符合目前肾病发病特点，见效快、服用方便、无任何副作用的治疗肾病的纯中药制剂。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    41,
    42
  ],
  "subject_type": "中药制剂",
  "object": [
    74,
    75
  ],
  "object_type": "成分"
}
```

### 样例7

文件：`中药专利数据集/test.json`；记录：`7`

原文：

本发明涉及一种具有健脑怡神、补中益气的中药保健制剂及其制备方法，该所述中药制剂的有效成分是由以下重量份数的原料制成：党参5～10份、黄芪10～20份、枸杞10～20份、淮山10～20份、当归10～20份、白芍10～20份、桔梗10～20份、沙参10～20份、麦冬20～30份、首乌20～30份、熟地20～30份、玄参5～10份、桂圆肉10～20份、红枣20～30份、黑枣10～20份、巴戟10～20份、杜仲10～20份、牛七20～30份、续断10～20份、菖蒲10～20份、远志10～20份等中药原料配制而成。本发明具有健脑怡神、补中益气的功效，同时还能补心、补肾壮阳、延缓衰老的功效等特点。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    35,
    38
  ],
  "subject_type": "中药制剂",
  "object": [
    66,
    67
  ],
  "object_type": "成分"
}
```

### 样例8

文件：`中药专利数据集/test.json`；记录：`8`

原文：

本发明涉及一种辅助降压的中药制剂的制备方法，包括以下步骤：将决明子粉加入乙醇中进行浸泡，然后依次加热至沸腾、抽滤、减压浓缩和喷雾干燥，获得决明子浸膏粉；将葛根粉加入红曲老醋中进行浸提，然后将浸提后的葛根粉与红曲老醋的混合液加入乙醇中进行超声提取，然后进行抽滤、浓缩和真空干燥粉碎，获得浸提醋制葛根粉；将所述决明子浸膏粉和浸提醋制葛根粉进行混合。本发明的辅助降压的中药制剂的制备方法获得的中药制剂具有清肝火、明目降压、有效缓解高血压所致的头昏目眩的功效。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    12,
    15
  ],
  "subject_type": "中药制剂",
  "object": [
    82,
    85
  ],
  "object_type": "成分"
}
```

### 样例9

文件：`中药专利数据集/test.json`；记录：`9`

原文：

本发明属于中药制剂领域，目的是根据中医治疗头痛的认识机理而提供的一种可有效治疗头痛的丸剂药物，所述药物的各个组分及其质量份比如下：钩藤60～350g、川芎30～120g、菊花100～160g、麻黄15～120g、麦冬（去心）60～160g、细辛15～90g、附子30～90g、白芍50～120g、羌活100～260g、天麻30～120g、独活30～120g、防风50～120g、天麻30～120g、地黄90～160g、牛膝50～160g、当归80～160g、鸡血藤100～160g、白术70～160g、桃仁80～160g、红花50～120g、白芷30～120g、郁金30～120g；本发明提供的药物是一个很好的中药组方。

原始关系标注：

```json
{
  "predicate": "包含",
  "subject": [
    49,
    50
  ],
  "subject_type": "中药制剂",
  "object": [
    138,
    139
  ],
  "object_type": "成分"
}
```

### 样例10

文件：`中药专利数据集/test.json`；记录：`10`

原文：

本发明公开了一种止泻中药配方，由以下原料药物制成：黄芪10～25份、麸炒神曲4～8份、艾蒿10～11份、黄连2～3份、银花3～4份、神曲6～7份、荆芥1～2份、无花果2～4份、生姜2～3份、木香1～8份。本发明为纯中药制剂，无毒副作用，通过各组分的协同作用，能够健脾祛湿、升阳止泻，适用于各类腹泻，具有适用广泛、效果好的优点。

原始关系标注：

```json
{
  "predicate": "功效",
  "subject": [
    102,
    104
  ],
  "subject_type": "中药制剂",
  "object": [
    131,
    134
  ],
  "object_type": "功效词"
}
```

## SanWen

来源：[数据页面](https://github.com/lancopku/Chinese-Literature-NER-RE-Dataset)

| 编号 | 主体 | 关系 | 客体 |
|---|---|---|---|
| 1 | 他 | Social | 他的助手 |
| 2 | 我 | Social | 其他云南同学 |
| 3 | 奥地利天才作曲家莫扎特 | Create | 一首原为德文的童声合唱曲 |
| 4 | 双脚 | Part-Whole | 我 |
| 5 | 孙子 | Family | 老曹 |
| 6 | 大街小巷 | Located | 浙西江山县城 |
| 7 | 砂中的金子 | Located | 砂中 |
| 8 | 那里的水 | Located | 那里 |
| 9 | 燕 | Located | 梁间 |
| 10 | 他 | Ownership | 学馆 |

### 样例1

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/1000.ann`；记录：`R1`

原文节选：

午八点正，几个学员专程拜访，请他解惑，恰见他的助手正在纳闷：怎么啦，老师一向提前

原始关系标注：

```json
"R1\tSocial Arg1:T101 Arg2:T102\t"
```

实体编号映射：

```json
{
  "T101": [
    "他",
    "Person-Pronoun 1691 1692"
  ],
  "T102": [
    "他的助手",
    "Person-Nominal 1697 1701"
  ]
}
```

### 样例2

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/1004.ann`；记录：`R1`

原文节选：

和赞誉：好美的花，好绿的叶!
我与其他云南同学对视骇笑，不自觉地带了些许怜悯

原始关系标注：

```json
"R1\tSocial Arg1:T8 Arg2:T9\t"
```

实体编号映射：

```json
{
  "T8": [
    "我",
    "Person-Pronoun 146 147"
  ],
  "T9": [
    "其他云南同学",
    "Person-Nominal 148 154"
  ]
}
```

### 样例3

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/1111.ann`；记录：`R1`

原文节选：

.596)，这是
一七九一年由奥地利天才作曲家莫扎特作曲、奥弗贝克作词的一首原为德文的童声合唱曲，表达了作者对春天的无限憧憬和

原始关系标注：

```json
"R1\tCreate Arg1:T13 Arg2:T27\t"
```

实体编号映射：

```json
{
  "T13": [
    "奥地利天才作曲家莫扎特",
    "Person-Name 106 117"
  ],
  "T27": [
    "一首原为德文的童声合唱曲",
    "Thing-Nominal 127 139"
  ]
}
```

### 样例4

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/1117.ann`；记录：`R1`

原文节选：

一下，一时间闪出退缩的念头。当我的双脚踏上澳大利亚时，原先想象的喜悦

原始关系标注：

```json
"R1\tPart-Whole Arg1:T11 Arg2:T12\t"
```

实体编号映射：

```json
{
  "T11": [
    "双脚",
    "Thing-Nominal 98 100"
  ],
  "T12": [
    "我",
    "Person-Pronoun 96 97"
  ]
}
```

### 样例5

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/112.ann`；记录：`R1`

原文节选：

月十六日，我去市郊城南村参加了老曹孙子的婚礼。
老曹和我同事，因她是

原始关系标注：

```json
"R1\tFamily Arg1:T4 Arg2:T5\t"
```

实体编号映射：

```json
{
  "T4": [
    "孙子",
    "Person-Nominal 20 22"
  ],
  "T5": [
    "老曹",
    "Person-Name 18 20"
  ]
}
```

### 样例6

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/12.ann`；记录：`R1`

原文节选：

到二十世纪六十年代初，你行走在浙西江山县城的大街小巷，或许就会碰到一个卖臭豆腐的女

原始关系标注：

```json
"R1\tLocated Arg1:T4 Arg2:T3\t"
```

实体编号映射：

```json
{
  "T4": [
    "大街小巷",
    "Thing-Nominal 32 36"
  ],
  "T3": [
    "浙西江山县城",
    "Location-Name 25 31"
  ]
}
```

### 样例7

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/120.ann`；记录：`R1`

原文节选：

，再也无从想起。惟有两句歌词，砂中的金子似的，在眼前闪着光，
轻抚的琴

原始关系标注：

```json
"R1\tLocated Arg1:T4 Arg2:T5\t"
```

实体编号映射：

```json
{
  "T4": [
    "砂中的金子",
    "Thing-Nominal 45 50"
  ],
  "T5": [
    "砂中",
    "Location-Nominal 45 47"
  ]
}
```

### 样例8

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/125.ann`；记录：`R1`

原文节选：

从西藏回来，我常忆难忘那里的水。倘若你尚未踏上过西藏的大地，

原始关系标注：

```json
"R1\tLocated Arg1:T3 Arg2:T4\t"
```

实体编号映射：

```json
{
  "T3": [
    "那里的水",
    "Thing-Nominal 11 15"
  ],
  "T4": [
    "那里",
    "Location-Pronoun 11 13"
  ]
}
```

### 样例9

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/131.ann`；记录：`R1`

原文节选：

不已，“你是一树一树的花开，是燕在梁间呢喃。你是爱，是暖
，是希望。

原始关系标注：

```json
"R1\tLocated Arg1:T12 Arg2:T13\t"
```

实体编号映射：

```json
{
  "T12": [
    "燕",
    "Thing-Nominal 47 48"
  ],
  "T13": [
    "梁间",
    "Location-Nominal 49 51"
  ]
}
```

### 样例10

文件：`Chinese-Literature-NER-RE-Dataset-master/relation_extraction/Testing/143.ann`；记录：`R1`

原文节选：

的重点建筑是湛若水的广州故居和他的学馆而得名。湛若水是明代大名鼎鼎的

原始关系标注：

```json
"R1\tOwnership Arg1:T6 Arg2:T7\t"
```

实体编号映射：

```json
{
  "T6": [
    "他",
    "Person-Pronoun 33 34"
  ],
  "T7": [
    "学馆",
    "Thing-Nominal 35 37"
  ]
}
```

## CMeIE

来源：[数据页面](https://huggingface.co/datasets/Aunderline/CMeIE/tree/main)

| 编号 | 主体 | 关系 | 客体 |
|---|---|---|---|
| 1 | 急性胰腺炎 | 影像学检查 | ERCP |
| 2 | 广泛性焦虑症 | 鉴别诊断 | 社交性焦虑 |
| 3 | 骨性关节炎 | 发病部位 | 关节 |
| 4 | 胆囊穿孔 | 死亡率 | 30% |
| 5 | 乙型肝炎 | 预防 | 不献血 |
| 6 | 心绞痛 | 药物治疗 | β受体阻滞剂 |
| 7 | 感染性心内膜炎 | 病因 | 链球菌 |
| 8 | 稳定型缺血性心脏疾病 | 药物治疗 | 高强度他汀类药物治疗 |
| 9 | 营养性巨幼细胞性贫血 | 药物治疗 | 维生素B12 |
| 10 | 原发性高血压 | 预防 | 适量的咖啡因摄入量 |

### 样例1

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`1`

原文：

急性胰腺炎@有研究显示，进行早期 ERCP （24 小时内）可以降低梗阻性胆总管结石患者的并发症发生率和死亡率； 但是，对于无胆总管梗阻的胆汁性急性胰腺炎患者，不需要进行早期 ERCP。

原始关系标注：

```json
{
  "Combined": false,
  "predicate": "影像学检查",
  "subject": "急性胰腺炎",
  "subject_type": "疾病",
  "object": {
    "@value": "ERCP"
  },
  "object_type": {
    "@value": "检查"
  }
}
```

### 样例2

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`2`

原文：

【诊断】 根据疾病诊断和统计手册第4版标准，焦虑情绪持续6个月以上，并至少下述4项症状： 1.担忧将来的意外事件； 2.担忧自己的能力； 3.担忧过去的行为； 4.躯体不适症状； 5.自我意识（对主体的自我认识）； 6.不断需要得到他人的确认； 7.持续紧张和（或）不能放松； 广泛性焦虑症影响社会交往，与分离性焦虑症比较，更多伴有其他焦虑症，如惊恐发作或单纯性恐怖症。 （二）社交性焦虑 尽管两种疾病均害怕在公众场合下说话，但广泛性焦虑也害怕对过去和将来情形的焦虑。

原始关系标注：

```json
{
  "Combined": true,
  "predicate": "鉴别诊断",
  "subject": "广泛性焦虑症",
  "subject_type": "疾病",
  "object": {
    "@value": "社交性焦虑"
  },
  "object_type": {
    "@value": "疾病"
  }
}
```

### 样例3

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`3`

原文：

骨性关节炎@在其他关节（如踝关节和腕关节），骨性关节炎比较少见，并且一般有潜在的病因（如结晶性关节病、创伤）。

原始关系标注：

```json
{
  "Combined": false,
  "predicate": "发病部位",
  "subject": "骨性关节炎",
  "subject_type": "疾病",
  "object": {
    "@value": "关节"
  },
  "object_type": {
    "@value": "部位"
  }
}
```

### 样例4

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`4`

原文：

胆囊炎@如果胆囊穿孔，死亡率为 30%。

原始关系标注：

```json
{
  "Combined": false,
  "predicate": "死亡率",
  "subject": "胆囊穿孔",
  "subject_type": "疾病",
  "object": {
    "@value": "30%"
  },
  "object_type": {
    "@value": "流行病学"
  }
}
```

### 样例5

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`5`

原文：

乙型肝炎@## 患者指导 HBsAg阳性的人性交时如果对方未接种疫苗或无自然免疫应采取防护，不应与他人共用牙刷或剃须刀，应遮盖开放的割伤和擦伤，使用漂白剂或洗涤剂清洁溢出血液，不献血、不捐献器官或精液。

原始关系标注：

```json
{
  "Combined": false,
  "predicate": "预防",
  "subject": "乙型肝炎",
  "subject_type": "疾病",
  "object": {
    "@value": "不献血"
  },
  "object_type": {
    "@value": "其他"
  }
}
```

### 样例6

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`6`

原文：

稳定型缺血性心脏疾病@ 现有的抗心绞痛药物 * 抗心绞痛药物的主要目标是减少心绞痛症状，改善生活质量。稳定型缺血性心脏疾病@ * β受体阻滞剂是一线用药，尤其是对于既往有心肌梗死或左心功能不全史的患者，因为β受体阻滞剂可降低这些患者未来心肌梗死或死亡的风险。

原始关系标注：

```json
{
  "Combined": true,
  "predicate": "药物治疗",
  "subject": "心绞痛",
  "subject_type": "疾病",
  "object": {
    "@value": "β受体阻滞剂"
  },
  "object_type": {
    "@value": "药物"
  }
}
```

### 样例7

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`7`

原文：

感染性心内膜炎@引起 ICU 中感染性心内膜炎的最常见病原体是葡萄球菌，其次是链球菌。感染性心内膜炎@ICU 中感染性心内膜炎的另外一个专有特点是真菌性感染性心内膜炎的发生率增高，因此，如果出现对抗生素治疗无反应的情况时，应考虑真菌性感染性心内膜炎。

原始关系标注：

```json
{
  "Combined": true,
  "predicate": "病因",
  "subject": "感染性心内膜炎",
  "subject_type": "疾病",
  "object": {
    "@value": "链球菌"
  },
  "object_type": {
    "@value": "社会学"
  }
}
```

### 样例8

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`8`

原文：

稳定型缺血性心脏疾病@ * 所有年龄超过 21 岁、LDL 大于或等于 190 的患者都应当接受高强度他汀类药物治疗。

原始关系标注：

```json
{
  "Combined": false,
  "predicate": "药物治疗",
  "subject": "稳定型缺血性心脏疾病",
  "subject_type": "疾病",
  "object": {
    "@value": "高强度他汀类药物治疗"
  },
  "object_type": {
    "@value": "药物"
  }
}
```

### 样例9

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`9`

原文：

营养性巨幼细胞性贫血（nutritional megaloblastic anemia)是由于维生素B12和（或）叶酸缺乏所致的一种大细胞性贫血。 维生素B12和叶酸治疗 有神经精神症状者,应以维生素Bl2治疗为主,如单用叶酸反而有加重症状的可能。

原始关系标注：

```json
{
  "Combined": true,
  "predicate": "药物治疗",
  "subject": "营养性巨幼细胞性贫血",
  "subject_type": "疾病",
  "object": {
    "@value": "维生素B12"
  },
  "object_type": {
    "@value": "药物"
  }
}
```

### 样例10

文件：`Aunderline/CMeIE/CMeIE_dev.jsonl`；记录：`10`

原文：

原发性高血压@ 因此，适量的咖啡因摄入量是可以接受的。

原始关系标注：

```json
{
  "Combined": false,
  "predicate": "预防",
  "subject": "原发性高血压",
  "subject_type": "疾病",
  "object": {
    "@value": "适量的咖啡因摄入量"
  },
  "object_type": {
    "@value": "其他"
  }
}
```

## Geology

来源：[数据页面](https://data.mendeley.com/datasets/mwwbc7cgy8/2)

| 编号 | 主体 | 关系 | 客体 |
|---|---|---|---|
| 1 | 地壳 | locate | 地球表层 |
| 2 | 工程地质学 | define_as | 介于地学与工程学之间的一门边缘交叉学科 |
| 3 | 工程地质条件 | involve | 地形地貌、地层岩性、地质构造、水文地质、自然地质作用与现象 |
| 4 | 滑坡 | affect | 建筑物 |
| 5 | 地震 | affect | 建筑物 |
| 6 | 平原地区 | has_condition | 土层较厚，且简单和均匀 |
| 7 | 山区 | has_condition | 地质条件复杂 |
| 8 | 挡墙 | mitigate | 滑坡 |
| 9 | 加强排水 | mitigate | 滑坡 |
| 10 | 砂页岩层 | has_risk | 基岩滑坡 |

### 样例1

文件：`Entity Training Set 2.json`；记录：`1.1`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "地壳",
  "head_type": "geological_environmental_conditions",
  "relation": "locate",
  "tail": "地球表层",
  "tail_type": "location"
}
```

### 样例2

文件：`Entity Training Set 2.json`；记录：`1.2`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "工程地质学",
  "head_type": "definition",
  "relation": "define_as",
  "tail": "介于地学与工程学之间的一门边缘交叉学科",
  "tail_type": "definition"
}
```

### 样例3

文件：`Entity Training Set 2.json`；记录：`1.3`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "工程地质条件",
  "head_type": "geological_environmental_conditions",
  "relation": "involve",
  "tail": "地形地貌、地层岩性、地质构造、水文地质、自然地质作用与现象",
  "tail_type": "geological_environmental_conditions"
}
```

### 样例4

文件：`Entity Training Set 2.json`；记录：`1.4`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "滑坡",
  "head_type": "disaster_type",
  "relation": "affect",
  "tail": "建筑物",
  "tail_type": "infrastructure"
}
```

### 样例5

文件：`Entity Training Set 2.json`；记录：`1.5`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "地震",
  "head_type": "disaster_type",
  "relation": "affect",
  "tail": "建筑物",
  "tail_type": "infrastructure"
}
```

### 样例6

文件：`Entity Training Set 2.json`；记录：`1.6`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "平原地区",
  "head_type": "location",
  "relation": "has_condition",
  "tail": "土层较厚，且简单和均匀",
  "tail_type": "geological_environmental_conditions"
}
```

### 样例7

文件：`Entity Training Set 2.json`；记录：`1.7`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "山区",
  "head_type": "location",
  "relation": "has_condition",
  "tail": "地质条件复杂",
  "tail_type": "geological_environmental_conditions"
}
```

### 样例8

文件：`Entity Training Set 2.json`；记录：`1.8`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "挡墙",
  "head_type": "mitigation",
  "relation": "mitigate",
  "tail": "滑坡",
  "tail_type": "disaster_type"
}
```

### 样例9

文件：`Entity Training Set 2.json`；记录：`1.9`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "加强排水",
  "head_type": "mitigation",
  "relation": "mitigate",
  "tail": "滑坡",
  "tail_type": "disaster_type"
}
```

### 样例10

文件：`Entity Training Set 2.json`；记录：`1.10`

原文：此JSON条目未提供对应原文。

原始关系标注：

```json
{
  "head": "砂页岩层",
  "head_type": "geological_environmental_conditions",
  "relation": "has_risk",
  "tail": "基岩滑坡",
  "tail_type": "disaster_type"
}
```
