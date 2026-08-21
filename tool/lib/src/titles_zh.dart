/// Chinese display titles for book pages.
///
/// Keys stay English so [toFileName] / markdown paths keep working.
const Map<String, String> chineseTitles = {
  "Crafting Interpreters": "解释器设计与实现",
  "Dedication": "献辞",
  "Acknowledgements": "致谢",
  "Table of Contents": "目录",
  "Welcome": "欢迎",
  "Introduction": "序言",
  "A Map of the Territory": "程序语言世界的地图",
  "The Lox Language": "Lox 程序设计语言",
  "A Tree-Walk Interpreter": "树遍历解释器",
  "Scanning": "扫描",
  "Representing Code": "表示代码",
  "Parsing Expressions": "解析表达式",
  "Evaluating Expressions": "求值表达式",
  "Statements and State": "语句与状态",
  "Control Flow": "控制流",
  "Functions": "函数",
  "Resolving and Binding": "解析与绑定",
  "Classes": "类",
  "Inheritance": "继承",
  "A Bytecode Virtual Machine": "字节码虚拟机",
  "Chunks of Bytecode": "字节码块",
  "A Virtual Machine": "虚拟机",
  "Scanning on Demand": "按需词法分析",
  "Compiling Expressions": "编译表达式",
  "Types of Values": "值的类型",
  "Strings": "字符串",
  "Hash Tables": "哈希表",
  "Global Variables": "全局变量",
  "Local Variables": "局部变量",
  "Jumping Back and Forth": "来回跳转",
  "Calls and Functions": "调用与函数",
  "Closures": "闭包",
  "Garbage Collection": "垃圾回收",
  "Classes and Instances": "类与实例",
  "Methods and Initializers": "方法与初始化器",
  "Superclasses": "超类",
  "Optimization": "优化",
  "Backmatter": "后记",
  "Appendix I": "附录 I",
  "Appendix II": "附录 II",
};

/// Returns the Chinese display title for an English page title.
String chineseDisplayTitle(String englishTitle) =>
    chineseTitles[englishTitle] ?? englishTitle;
