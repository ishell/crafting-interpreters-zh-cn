# 类与实例

<!--
> Caring too much for objects can destroy you. Only -- if you care for a thing
> enough, it takes on a life of its own, doesn't it? And isn’t the whole point
> of things -- beautiful things -- that they connect you to some larger beauty?
>
> <cite>Donna Tartt, <em>The Goldfinch</em></cite>
-->
> 对物件太过倾心，会毁了你。只是——若你对一样东西足够在意，它岂不就有了自己的生命？而物件——美的物件——的全部意义，不正是把你连向某种更大的美吗？
>
> <cite>唐娜·塔特，<em>《金翅雀》</em></cite>

<!--
The last area left to implement in clox is object-oriented programming. <span
name="oop">OOP</span> is a bundle of intertwined features: classes, instances,
fields, methods, initializers, and inheritance. Using relatively high-level
Java, we packed all that into two chapters. Now that we're coding in C, which
feels like building a model of the Eiffel tower out of toothpicks, we'll devote
three chapters to covering the same territory. This makes for a leisurely stroll
through the implementation. After strenuous chapters like [closures][] and the
[garbage collector][], you have earned a rest. In fact, the book should be easy
from here on out.
-->
clox 里还剩最后一块要落地：面向对象编程。<span name="oop">OOP</span>是一束缠在一起的特性：类、实例、字段、方法、初始化器，还有继承。用相对高层的 Java 时，我们把这一切塞进了两章。如今在 C 里写——感觉像用牙签搭埃菲尔铁塔模型——我们会用三章走完同一片领地。这样实现路上可以悠闲散步。在[闭包][closures]和[垃圾回收器][garbage collector]那种烧脑章节之后，你也该歇一歇了。其实从这儿往后，这本书该轻松起来了。

<aside name="oop">

<!--
People who have strong opinions about object-oriented programming -- read
"everyone" -- tend to assume OOP means some very specific list of language
features, but really there's a whole space to explore, and each language has its
own ingredients and recipes.

Self has objects but no classes. CLOS has methods but doesn't attach them to
specific classes. C++ initially had no runtime polymorphism -- no virtual
methods. Python has multiple inheritance, but Java does not. Ruby attaches
methods to classes, but you can also define methods on a single object.
-->
对面向对象编程抱有强烈意见的人——读作“所有人”——往往假定 OOP 就是某张很具体的语言特性清单；其实那里有一整片空间可探索，每种语言都有自己的食材与菜谱。

Self 有对象却没有类。CLOS 有方法，却不把方法挂到特定类上。C++ 起初没有运行时多态——没有虚方法。Python 有多重继承，Java 没有。Ruby 把方法挂到类上，但你也可以在单个对象上定义方法。

</aside>

<!--
In this chapter, we cover the first three features: classes, instances, and
fields. This is the stateful side of object orientation. Then in the next two
chapters, we will hang behavior and code reuse off of those objects.
-->
本章覆盖前三项特性：类、实例和字段。这是面向对象的有状态一面。接下来两章，我们再把行为与代码复用挂到这些对象上。

[closures]: closures.html
[garbage collector]: garbage-collection.html

<!--
-- Class Objects
-->
## 类对象

<!--
In a class-based object-oriented language, everything begins with classes. They
define what sorts of objects exist in the program and are the factories used to
produce new instances. Going bottom-up, we'll start with their runtime
representation and then hook that into the language.
-->
在基于类的面向对象语言里，一切从类开始。它们界定程序里存在哪些种类的对象，也是生产新实例的工厂。我们自下而上：先做它们的运行时表示，再接到语言里。

<!--
By this point, we're well-acquainted with the process of adding a new object
type to the VM. We start with a struct.
-->
到这一步，给虚拟机加一种新对象类型，我们已经很熟了。从结构体开始。

^code obj-class (1 before, 2 after)

<!--
After the Obj header, we store the class's name. This isn't strictly needed for
the user's program, but it lets us show the name at runtime for things like
stack traces.
-->
在 Obj 头之后，我们存放类的名字。用户程序严格来说并不需要它，但运行时——比如栈追踪——就能把名字显示出来。

<!--
The new type needs a corresponding case in the ObjType enum.
-->
新类型需要在 ObjType 枚举里有对应的一项。

^code obj-type-class (1 before, 1 after)

<!--
And that type gets a corresponding pair of macros. First, for testing an
object's type:
-->
这个类型还要配一对宏。先是用来测试对象类型的：

^code is-class (2 before, 1 after)

<!--
And then for casting a Value to an ObjClass pointer:
-->
然后是把 Value 转成 ObjClass 指针：

^code as-class (2 before, 1 after)

<!--
The VM creates new class objects using this function:
-->
虚拟机用这个函数创建新的类对象：

^code new-class-h (2 before, 1 after)

<!--
The implementation lives over here:
-->
实现在这边：

^code new-class

<!--
Pretty much all boilerplate. It takes in the class's name as a string and stores
it. Every time the user declares a new class, the VM will create a new one of
these ObjClass structs to represent it.
-->
几乎全是样板代码。它接收类名字符串并存起来。用户每声明一个新类，虚拟机就创建一个这样的 ObjClass 结构来表示它。

<aside name="klass">

<img src="image/classes-and-instances/klass.png" alt="'Klass' in a zany kidz font."/>

<!--
I named the variable "klass" not just to give the VM a zany preschool "Kidz
Korner" feel. It makes it easier to get clox compiling as C++ where "class" is
a reserved word.
-->
我把变量叫 “klass”，不只是为了给虚拟机一点幼稚园 “Kidz Korner” 的荒诞感。这样也更容易让 clox 作为 C++ 编译——在那儿 `class` 是保留字。

</aside>

<!--
When the VM no longer needs a class, it frees it like so:
-->
虚拟机不再需要某个类时，就这样释放它：

^code free-class (1 before, 1 after)

<aside name="braces">

<!--
The braces here are pointless now, but will be useful in the next chapter when
we add some more code to the switch case.
-->
这里的花括号眼下毫无意义，但下一章我们往这个 switch case 里再塞代码时，就会派上用场。

</aside>

<!--
We have a memory manager now, so we also need to support tracing through class
objects.
-->
我们现在有内存管理器了，所以还要支持对类对象的追踪。

^code blacken-class (1 before, 1 after)

<!--
When the GC reaches a class object, it marks the class's name to keep that
string alive too.
-->
GC 到达一个类对象时，会标记类的名字，好让那根字符串也活着。

<!--
The last operation the VM can perform on a class is printing it.
-->
虚拟机对类能做的最后一项操作，是打印它。

^code print-class (1 before, 1 after)

<!--
A class simply says its own name.
-->
类只是说出自己的名字。

<!--
-- Class Declarations
-->
## 类声明

<!--
Runtime representation in hand, we are ready to add support for classes to the
language. Next, we move into the parser.
-->
运行时表示到手，我们准备给语言加上对类的支持。下一步，走进解析器。

^code match-class (1 before, 1 after)

<!--
Class declarations are statements, and the parser recognizes one by the leading
`class` keyword. The rest of the compilation happens over here:
-->
类声明是语句，解析器靠前导的 `class` 关键字认出它。其余编译工作在这边：

^code class-declaration

<!--
Immediately after the `class` keyword is the class's name. We take that
identifier and add it to the surrounding function's constant table as a string.
As you just saw, printing a class shows its name, so the compiler needs to stuff
the name string somewhere that the runtime can find. The constant table is the
way to do that.
-->
紧跟在 `class` 关键字后面的是类名。我们取那个标识符，作为字符串加进外围函数的常量表。你刚看到，打印类会显示它的名字，所以编译器得把名字字符串塞到运行时找得到的地方。常量表就是干这事的。

<!--
The class's <span name="variable">name</span> is also used to bind the class
object to a variable of the same name. So we declare a variable with that
identifier right after consuming its token.
-->
类的<span name="variable">名字</span>还用来把类对象绑定到同名变量上。所以我们在吃掉那个 token 之后，立刻用该标识符声明一个变量。

<aside name="variable">

<!--
We could have made class declarations be *expressions* instead of statements --
they are essentially a literal that produces a value after all. Then users would
have to explicitly bind the class to a variable themselves like:
-->
我们本可以把类声明做成*表达式*而不是语句——毕竟它们本质上就是产生值的字面量。那样用户就得自己显式把类绑到变量上，比如：

```lox
var Pie = class {}
```

<!--
Sort of like lambda functions but for classes. But since we generally want
classes to be named anyway, it makes sense to treat them as declarations.
-->
有点像给类用的 lambda。不过我们本来就通常希望类有名字，所以把它们当声明处理更说得通。

</aside>

<!--
Next, we emit a new instruction to actually create the class object at runtime.
That instruction takes the constant table index of the class's name as an
operand.
-->
接下来，我们发出一条新指令，在运行时真正创建类对象。该指令以类名在常量表中的索引作为操作数。

<!--
After that, but before compiling the body of the class, we define the variable
for the class's name. *Declaring* the variable adds it to the scope, but recall
from [a previous chapter][scope] that we can't *use* the variable until it's
*defined*. For classes, we define the variable before the body. That way, users
can refer to the containing class inside the bodies of its own methods. That's
useful for things like factory methods that produce new instances of the class.
-->
在那之后、编译类体之前，我们定义类名对应的变量。*声明*变量会把它加进作用域，但请回想[前一章][scope]：变量要等到被*定义*之后才能*使用*。对类，我们在类体之前就定义变量。这样，用户可以在类自身方法的函数体里引用包含它的那个类——对生产该类新实例的工厂方法之类很有用。

[scope]: local-variables.html#another-scope-edge-case

<!--
Finally, we compile the body. We don't have methods yet, so right now it's
simply an empty pair of braces. Lox doesn't require fields to be declared in the
class, so we're done with the body -- and the parser -- for now.
-->
最后，编译类体。我们还没有方法，所以眼下只是一对空花括号。Lox 不要求在类里声明字段，所以类体——以及解析器——暂时就到这儿。

<!--
The compiler is emitting a new instruction, so let's define that.
-->
编译器在发出一条新指令，我们来定义它。

^code class-op (1 before, 1 after)

<!--
And add it to the disassembler:
-->
再加进反汇编器：

^code disassemble-class (2 before, 1 after)

<!--
For such a large-seeming feature, the interpreter support is minimal.
-->
对一项看起来这么大的特性来说，解释器这边的支持少得可怜。

^code interpret-class (2 before, 1 after)

<!--
We load the string for the class's name from the constant table and pass that to
`newClass()`. That creates a new class object with the given name. We push that
onto the stack and we're good. If the class is bound to a global variable, then
the compiler's call to `defineVariable()` will emit code to store that object
from the stack into the global variable table. Otherwise, it's right where it
needs to be on the stack for a new <span name="local">local</span> variable.
-->
我们从常量表加载类名字符串，传给 `newClass()`。那会创建一个带该名字的新类对象。我们把它压进栈，就齐了。若类绑定到全局变量，编译器对 `defineVariable()` 的调用会发出代码，把栈上那个对象存进全局变量表。否则，它正停在栈上新<span name="local">局部</span>变量该在的位置。

<aside name="local">

<!--
"Local" classes -- classes declared inside the body of a function or block, are
an unusual concept. Many languages don't allow them at all. But since Lox is a
dynamically typed scripting language, it treats the top level of a program and
the bodies of functions and blocks uniformly. Classes are just another kind of
declaration, and since you can declare variables and functions inside blocks,
you can declare classes in there too.
-->
“局部”类——声明在函数或代码块体内的类——是个不太寻常的概念。许多语言根本不允许。但 Lox 是动态类型的脚本语言，它把程序顶层与函数、代码块的体一视同仁。类只是另一种声明；既然你可以在代码块里声明变量和函数，也可以在那儿声明类。

</aside>

<!--
There you have it, our VM supports classes now. You can run this:
-->
好了，我们的虚拟机现在支持类了。你可以跑这个：

```lox
class Brioche {}
print Brioche;
```

<!--
Unfortunately, printing is about *all* you can do with classes, so next is
making them more useful.
-->
可惜，打印几乎就是你对类*全部*能干的事了，所以下一步是让它们更有用。

<!--
-- Instances of Classes
-->
## 类的实例

<!--
Classes serve two main purposes in a language:
-->
类在语言里主要干两件事：

<!--
*   **They are how you create new instances.** Sometimes this involves a `new`
    keyword, other times it's a method call on the class object, but you usually
    mention the class by name *somehow* to get a new instance.

*   **They contain methods.** These define how all instances of the class
    behave.
-->
*   **它们是你创建新实例的途径。**有时要靠 `new` 关键字，有时是对类对象的方法调用，但你通常会*以某种方式*点名那个类，才能得到新实例。

*   **它们容纳方法。**这些方法界定该类所有实例如何行为。

<!--
We won't get to methods until the next chapter, so for now we will only worry
about the first part. Before classes can create instances, we need a
representation for them.
-->
方法要等到下一章，所以眼下我们只操心第一部分。类要能创建实例之前，我们需要实例的表示。

^code obj-instance (1 before, 2 after)

<!--
Instances know their class -- each instance has a pointer to the class that it
is an instance of.  We won't use this much in this chapter, but it will become
critical when we add methods.
-->
实例知道自己的类——每个实例都有指向它所实例化的那个类的指针。本章用不了多少，但加上方法之后它会变得至关重要。

<!--
More important to this chapter is how instances store their state. Lox lets
users freely add fields to an instance at runtime. This means we need a storage
mechanism that can grow. We could use a dynamic array, but we also want to look
up fields by name as quickly as possible. There's a data structure that's just
perfect for quickly accessing a set of values by name and
-- even more conveniently -- we've already implemented it. Each instance stores
its fields using a hash table.
-->
对本来说更重要的，是实例如何存放状态。Lox 允许用户在运行时自由给实例加字段。这意味着我们需要能增长的存储机制。可以用动态数组，但我们还想按名字尽快查找字段。有一种数据结构正好擅长按名字快速访问一组值——更方便的是——我们已经实现过了。每个实例用哈希表存放自己的字段。

<aside name="fields">

<!--
Being able to freely add fields to an object at runtime is a big practical
difference between most dynamic and static languages. Statically typed languages
usually require fields to be explicitly declared. This way, the compiler knows
exactly what fields each instance has. It can use that to determine the precise
amount of memory needed for each instance and the offsets in that memory where
each field can be found.

In Lox and other dynamic languages, accessing a field is usually a hash table
lookup. Constant time, but still pretty heavyweight. In a language like C++,
accessing a field is as fast as offsetting a pointer by an integer constant.
-->
能在运行时自由给对象加字段，是多数动态语言与静态语言之间一个很大的实际差别。静态类型语言通常要求显式声明字段。这样编译器确切知道每个实例有哪些字段，从而算出每个实例精确需要多少内存，以及每个字段在内存里的偏移。

在 Lox 和其他动态语言里，访问字段通常是一次哈希表查找。常量时间，但仍然相当沉重。在像 C++ 这样的语言里，访问字段快得就像用一个整型常量去偏移指针。

</aside>

<!--
We only need to add an include, and we've got it.
-->
只需加一条 include，我们就有了。

^code object-include-table (1 before, 1 after)

<!--
This new struct gets a new object type.
-->
这个新结构体对应一种新的对象类型。

^code obj-type-instance (1 before, 1 after)

<!--
I want to slow down a bit here because the Lox *language's* notion of "type" and
the VM *implementation's* notion of "type" brush against each other in ways that
can be confusing. Inside the C code that makes clox, there are a number of
different types of Obj -- ObjString, ObjClosure, etc. Each has its own internal
representation and semantics.

In the Lox *language*, users can define their own classes -- say Cake and Pie --
and then create instances of those classes. From the user's perspective, an
instance of Cake is a different type of object than an instance of Pie. But,
from the VM's perspective, every class the user defines is simply another value
of type ObjClass. Likewise, each instance in the user's program, no matter what
class it is an instance of, is an ObjInstance. That one VM object type covers
instances of all classes. The two worlds map to each other something like this:
-->
我想在这儿放慢一点，因为 Lox *语言*里的“类型”概念，和虚拟机*实现*里的“类型”概念会擦肩而过，容易搅混。在构成 clox 的 C 代码里，有若干种不同的 Obj——ObjString、ObjClosure 等等。各自有内部表示与语义。

在 Lox *语言*里，用户可以定义自己的类——比方说 Cake 和 Pie——再创建那些类的实例。从用户视角看，Cake 的实例和 Pie 的实例是不同类型的对象。但在虚拟机看来，用户定义的每个类，只不过是类型为 ObjClass 的又一个值。同样，用户程序里的每个实例，无论它是哪个类的实例，都是一个 ObjInstance。那一种虚拟机对象类型覆盖了所有类的实例。两个世界彼此映射，大致像这样：

<img src="image/classes-and-instances/lox-clox.png" alt="A set of class declarations and instances, and the runtime representations each maps to."/>

<!--
Got it? OK, back to the implementation. We also get our usual macros.
-->
明白了？好，回到实现。我们也有惯常的那对宏。

^code is-instance (1 before, 1 after)

<!--
And:
-->
以及：

^code as-instance (1 before, 1 after)

<!--
Since fields are added after the instance is created, the "constructor" function
only needs to know the class.
-->
字段是在实例创建之后才加上的，所以“构造”函数只需要知道类。

^code new-instance-h (1 before, 1 after)

<!--
We implement that function here:
-->
我们在这儿实现那个函数：

^code new-instance

<!--
We store a reference to the instance's class. Then we initialize the field
table to an empty hash table. A new baby object is born!
-->
我们存一份对实例所属类的引用。然后把字段表初始化为空哈希表。一个崭新的小对象诞生了！

<!--
At the sadder end of the instance's lifespan, it gets freed.
-->
在实例寿命更忧伤的那一头，它会被释放。

^code free-instance (3 before, 1 after)

<!--
The instance owns its field table so when freeing the instance, we also free the
table. We don't explicitly free the entries *in* the table, because there may
be other references to those objects. The garbage collector will take care of
those for us. Here we free only the entry array of the table itself.
-->
实例拥有自己的字段表，所以释放实例时也释放那张表。我们不显式释放表*里*的条目，因为那些对象可能还有别的引用。垃圾回收器会替我们照看。这里只释放表本身的条目数组。

<!--
Speaking of the garbage collector, it needs support for tracing through
instances.
-->
说到垃圾回收器，它需要支持对实例的追踪。

^code blacken-instance (3 before, 1 after)

<!--
If the instance is alive, we need to keep its class around. Also, we need to
keep every object referenced by the instance's fields. Most live objects that
are not roots are reachable because some instance refers to the object in a
field. Fortunately, we already have a nice `markTable()` function to make
tracing them easy.
-->
若实例还活着，我们需要保住它的类。还要保住实例字段所引用的每一个对象。多数非根的存活对象之所以可达，正是因为某个实例在字段里引用了它。幸好我们已经有了漂亮的 `markTable()` 函数，追踪起来很轻松。

<!--
Less critical but still important is printing.
-->
没那么关键、但仍然重要的是打印。

^code print-instance (1 before, 1 after)

<!--
<span name="print">An</span> instance prints its name followed by "instance".
(The "instance" part is mainly so that classes and instances don't print the
same.)
-->
<span name="print">实例</span>打印自己的名字，再跟上 “instance”。（“instance” 这部分主要是为了让类和实例打印出来不一样。）

<aside name="print">

<!--
Most object-oriented languages let a class define some sort of `toString()`
method that lets the class specify how its instances are converted to a string
and printed. If Lox was less of a toy language, I would want to support that
too.
-->
多数面向对象语言允许类定义某种 `toString()` 方法，让类自己规定实例如何转成字符串并打印。若 Lox 不那么像玩具语言，我也想支持那个。

</aside>

<!--
The real fun happens over in the interpreter. Lox has no special `new` keyword.
The way to create an instance of a class is to invoke the class itself as if it
were a function. The runtime already supports function calls, and it checks the
type of object being called to make sure the user doesn't try to invoke a number
or other invalid type.

We extend that runtime checking with a new case.
-->
真正好玩的在解释器那边。Lox 没有特殊的 `new` 关键字。创建类实例的方式，是把类本身当作函数来调用。运行时已经支持函数调用，并会检查被调用对象的类型，确保用户不会去调用数字或其他无效类型。

我们给那套运行时检查加一个新分支。

^code call-class (1 before, 1 after)

<!--
If the value being called -- the object that results when evaluating the
expression to the left of the opening parenthesis -- is a class, then we treat
it as a constructor call. We <span name="args">create</span> a new instance of
the called class and store the result on the stack.
-->
若被调用的值——求值左括号左边那个表达式得到的对象——是一个类，我们就把它当作构造调用。我们<span name="args">创建</span>被调类的一个新实例，并把结果放在栈上。

<aside name="args">

<!--
We ignore any arguments passed to the call for now. We'll revisit this code in
the [next chapter][next] when we add support for initializers.
-->
眼下我们忽略传给调用的任何参数。等[下一章][next]加上对初始化器的支持时，我们会再回到这段代码。

[next]: methods-and-initializers.html

</aside>

<!--
We're one step farther. Now we can define classes and create instances of them.
-->
我们又前进了一步。现在可以定义类，并创建它们的实例了。

```lox
class Brioche {}
print Brioche();
```

<!--
Note the parentheses after `Brioche` on the second line now. This prints
"Brioche instance".
-->
注意第二行 `Brioche` 后面现在有括号了。这会打印 “Brioche instance”。

<!--
-- Get and Set Expressions
-->
## 取值与赋值表达式

<!--
Our object representation for instances can already store state, so all that
remains is exposing that functionality to the user. Fields are accessed and
modified using get and set expressions. Not one to break with tradition, Lox
uses the classic "dot" syntax:
-->
实例的对象表示已经能存状态了，剩下的只是把这能力暴露给用户。字段通过取值与赋值表达式来访问和修改。Lox 不爱破例，仍用经典的“点”语法：

```lox
eclair.filling = "pastry creme";
print eclair.filling;
```

<!--
The period -- full stop for my English friends -- works <span
name="sort">sort</span> of like an infix operator. There is an expression to the
left that is evaluated first and produces an instance. After that is the `.`
followed by a field name. Since there is a preceding operand, we hook this into
the parse table as an infix expression.
-->
这个句点——我英国朋友口中的 full stop——<span name="sort">有点</span>像中缀运算符。左边有个表达式，先求值，得到一个实例。后面是 `.`，再跟字段名。既然前面有操作数，我们就把它挂进解析表，当作中缀表达式。

<aside name="sort">

<!--
I say "sort of" because the right-hand side after the `.` is not an expression,
but a single identifier whose semantics are handled by the get or set expression
itself. It's really closer to a postfix expression.
-->
我说“有点”，是因为 `.` 右边不是表达式，而是单个标识符，其语义由取值或赋值表达式自己处理。其实更接近后缀表达式。

</aside>

^code table-dot (1 before, 1 after)

<!--
As in other languages, the `.` operator binds tightly, with precedence as high
as the parentheses in a function call. After the parser consumes the dot token,
it dispatches to a new parse function.
-->
和其他语言一样，`.` 运算符结合得很紧，优先级与函数调用的括号一样高。解析器吃掉点号 token 之后，分派到一个新的解析函数。

^code compile-dot

<!--
The parser expects to find a <span name="prop">property</span> name immediately
after the dot. We load that token's lexeme into the constant table as a string
so that the name is available at runtime.
-->
解析器期望在点号之后立刻找到一个<span name="prop">属性</span>名。我们把那个 token 的词素作为字符串载入常量表，好让运行时能拿到名字。

<aside name="prop">

<!--
The compiler uses "property" instead of "field" here because, remember, Lox also
lets you use dot syntax to access a method without calling it. "Property" is the
general term we use to refer to any named entity you can access on an instance.
Fields are the subset of properties that are backed by the instance's state.
-->
编译器这里用 “property”（属性）而不是 “field”（字段），因为——记住——Lox 也允许用点语法访问方法而不调用它。“属性”是我们用来指称实例上任何可访问的具名实体的总称。字段是由实例状态支撑的那一部分属性。

</aside>

<!--
We have two new expression forms -- getters and setters -- that this one
function handles. If we see an equals sign after the field name, it must be a
set expression that is assigning to a field. But we don't *always* allow an
equals sign after the field to be compiled. Consider:
-->
我们有两种新表达式形式——取值器与赋值器——由这一个函数处理。若字段名后面看到等号，那一定是给字段赋值的赋值表达式。但我们并不*总是*允许在字段后面编译等号。想想：

```lox
a + b.c = 3
```

<!--
This is syntactically invalid according to Lox's grammar, which means our Lox
implementation is obligated to detect and report the error. If `dot()` silently
parsed the `= 3` part, we would incorrectly interpret the code as if the user
had written:
-->
按 Lox 的文法，这在语法上无效，意味着我们的 Lox 实现有义务检测并报告错误。若 `dot()` 默默解析了 `= 3` 那部分，我们就会错误地把代码理解成用户写的是：

```lox
a + (b.c = 3)
```

<!--
The problem is that the `=` side of a set expression has much lower precedence
than the `.` part. The parser may call `dot()` in a context that is too high
precedence to permit a setter to appear. To avoid incorrectly allowing that, we
parse and compile the equals part only when `canAssign` is true. If an equals
token appears when `canAssign` is false, `dot()` leaves it alone and returns. In
that case, the compiler will eventually unwind up to `parsePrecedence()`, which
stops at the unexpected `=` still sitting as the next token and reports an
error.
-->
问题在于，赋值表达式里 `=` 那一侧的优先级远低于 `.` 那一侧。解析器可能在优先级过高、不允许出现赋值器的上下文里调用 `dot()`。为避免错误地放行，我们只在 `canAssign` 为真时才解析并编译等号部分。若 `canAssign` 为假时出现等号 token，`dot()` 就放过它并返回。那样的话，编译器最终会回退到 `parsePrecedence()`，它会停在仍作为下一个 token 坐着的那个意外的 `=` 上，并报告错误。

<!--
If we find an `=` in a context where it *is* allowed, then we compile the
expression that follows. After that, we emit a new <span
name="set">`OP_SET_PROPERTY`</span> instruction. That takes a single operand for
the index of the property name in the constant table. If we didn't compile a set
expression, we assume it's a getter and emit an `OP_GET_PROPERTY` instruction,
which also takes an operand for the property name.
-->
若我们在*允许*的上下文里找到 `=`，就编译后面的表达式。然后发出一条新的 <span name="set">`OP_SET_PROPERTY`</span> 指令。它带一个操作数：属性名在常量表中的索引。若我们没有编译赋值表达式，就假定是取值器，发出 `OP_GET_PROPERTY` 指令，同样带属性名操作数。

<aside name="set">

<!--
You can't *set* a non-field property, so I suppose that instruction could have
been `OP_SET_FIELD`, but I thought it looked nicer to be consistent with the get
instruction.
-->
你没法给非字段属性*赋值*，所以那条指令本可以叫 `OP_SET_FIELD`，但我觉得和 get 指令保持一致更好看。

</aside>

<!--
Now is a good time to define these two new instructions.
-->
现在正好定义这两条新指令。

^code property-ops (1 before, 1 after)

<!--
And add support for disassembling them:
-->
再为它们加上反汇编支持：

^code disassemble-property-ops (1 before, 1 after)

<!--
-- Interpreting getter and setter expressions
-->
### 解释取值与赋值表达式

<!--
Sliding over to the runtime, we'll start with get expressions since those are a
little simpler.
-->
滑到运行时这边，我们先从取值表达式开始，因为它们稍简单些。

^code interpret-get-property (1 before, 1 after)

<!--
When the interpreter reaches this instruction, the expression to the left of the
dot has already been executed and the resulting instance is on top of the stack.
We read the field name from the constant pool and look it up in the instance's
field table. If the hash table contains an entry with that name, we pop the
instance and push the entry's value as the result.
-->
解释器到达这条指令时，点号左边的表达式已经执行完，得到的实例在栈顶。我们从常量池读出字段名，在实例的字段表里查找。若哈希表里有同名条目，就弹出实例，把条目的值作为结果压栈。

<!--
Of course, the field might not exist. In Lox, we've defined that to be a runtime
error. So we add a check for that and abort if it happens.
-->
当然，字段也可能不存在。在 Lox 里，我们把这定义为运行时错误。所以加上检查，一旦发生就中止。

^code get-undefined (3 before, 2 after)

<!--
<span name="field">There</span> is another failure mode to handle which you've
probably noticed. The above code assumes the expression to the left of the dot
did evaluate to an ObjInstance. But there's nothing preventing a user from
writing this:
-->
<span name="field">还有</span>一种失败模式要处理，你大概已经注意到了。上面的代码假定点号左边的表达式确实求值成了 ObjInstance。但没有什么能阻止用户写出这个：

```lox
var obj = "not an instance";
print obj.field;
```

<!--
The user's program is wrong, but the VM still has to handle it with some grace.
Right now, it will misinterpret the bits of the ObjString as an ObjInstance and,
I don't know, catch on fire or something definitely not graceful.

In Lox, only instances are allowed to have fields. You can't stuff a field onto
a string or number. So we need to check that the value is an instance before
accessing any fields on it.
-->
用户程序是错的，但虚拟机仍须带着几分体面去处理。眼下，它会把 ObjString 的那些比特误当成 ObjInstance，然后——我不知道——着火，或干出别的绝对不体面的事。

在 Lox 里，只有实例可以有字段。你不能往字符串或数字上塞字段。所以在访问任何字段之前，我们需要检查那个值确是实例。

<aside name="field">

<!--
Lox *could* support adding fields to values of other types. It's our language
and we can do what we want. But it's likely a bad idea. It significantly
complicates the implementation in ways that hurt performance -- for example,
string interning gets a lot harder.

Also, it raises gnarly semantic questions around the equality and identity of
values. If I attach a field to the number `3`, does the result of `1 + 2` have
that field as well? If so, how does the implementation track that? If not, are
those two resulting "threes" still considered equal?
-->
Lox *可以*支持给其他类型的值加字段。这是我们的语言，想怎样就怎样。但这多半是个坏主意。它会显著复杂化实现，并伤及性能——比方说，字符串驻留会难得多。

它还会在值的相等与同一性周围掀起棘手的语义问题。若我给数字 `3` 挂上一个字段，`1 + 2` 的结果是否也有那个字段？若有，实现如何追踪？若没有，那两个得到的“三”是否仍视为相等？

</aside>

^code get-not-instance (1 before, 1 after)

<!--
If the value on the stack isn't an instance, we report a runtime error and
safely exit.
-->
若栈上的值不是实例，我们报告运行时错误并安全退出。

<!--
Of course, get expressions are not very useful when no instances have any
fields. For that we need setters.
-->
当然，若没有任何实例有字段，取值表达式也没多大用。为此我们需要赋值器。

^code interpret-set-property (2 before, 1 after)

<!--
This is a little more complex than `OP_GET_PROPERTY`. When this executes, the
top of the stack has the instance whose field is being set and above that, the
value to be stored. Like before, we read the instruction's operand and find the
field name string. Using that, we store the value on top of the stack into the
instance's field table.
-->
这比 `OP_GET_PROPERTY` 稍复杂一点。执行时，栈顶是正在被设置字段的实例，再上面是要存入的值。和之前一样，我们读指令的操作数，找到字段名字符串。用它把栈顶的值存进实例的字段表。

<!--
After that is a little <span name="stack">stack</span> juggling. We pop the
stored value off, then pop the instance, and finally push the value back on. In
other words, we remove the *second* element from the stack while leaving the top
alone. A setter is itself an expression whose result is the assigned value, so
we need to leave that value on the stack. Here's what I mean:
-->
之后是一点<span name="stack">栈</span>上的杂耍。我们弹出已存入的值，再弹出实例，最后把值压回去。换句话说，我们从栈上拿掉*第二个*元素，同时让栈顶原封不动。赋值器本身也是表达式，其结果就是被赋的值，所以我们需要把那个值留在栈上。我的意思是：

<aside name="stack">

<!--
The stack operations go like this:
-->
栈操作是这样的：

<img src="image/classes-and-instances/stack.png" alt="Popping two values and then pushing the first value back on the stack."/>

</aside>

```lox
class Toast {}
var toast = Toast();
print toast.jam = "grape"; // Prints "grape".
```

<!--
Unlike when reading a field, we don't need to worry about the hash table not
containing the field. A setter implicitly creates the field if needed. We do
need to handle the user incorrectly trying to store a field on a value that
isn't an instance.
-->
和读字段不同，我们不必担心哈希表里没有该字段。赋值器在需要时会隐式创建字段。我们确实需要处理用户错误地试图往非实例值上存字段的情况。

^code set-not-instance (1 before, 1 after)

<!--
Exactly like with get expressions, we check the value's type and report a
runtime error if it's invalid. And, with that, the stateful side of Lox's
support for object-oriented programming is in place. Give it a try:
-->
和取值表达式一模一样：检查值的类型，无效就报告运行时错误。至此，Lox 面向对象支持中有状态的那一面就位了。试试看：

```lox
class Pair {}

var pair = Pair();
pair.first = 1;
pair.second = 2;
print pair.first + pair.second; // 3.
```

<!--
This doesn't really feel very *object*-oriented. It's more like a strange,
dynamically typed variant of C where objects are loose struct-like bags of data.
Sort of a dynamic procedural language. But this is a big step in expressiveness.
Our Lox implementation now lets users freely aggregate data into bigger units.
In the next chapter, we will breathe life into those inert blobs.
-->
这其实不太像*面向*对象。更像一种古怪的、动态类型的 C 变体：对象是松散的、结构体似的数据包。有点像动态过程式语言。但这在表达力上是一大步。我们的 Lox 实现现在允许用户把数据自由聚合成更大的单元。下一章，我们会给这些惰性的团块注入生命。

<div class="challenges">

<!--
-- Challenges
-->
## 挑战

<!--
1.  Trying to access a non-existent field on an object immediately aborts the
    entire VM. The user has no way to recover from this runtime error, nor is
    there any way to see if a field exists *before* trying to access it. It's up
    to the user to ensure on their own that only valid fields are read.

    How do other dynamically typed languages handle missing fields? What do you
    think Lox should do? Implement your solution.
-->
1.  试图访问对象上不存在的字段会立刻中止整个虚拟机。用户无从从这个运行时错误中恢复，也没有任何办法在访问*之前*查看字段是否存在。只能靠用户自己确保只读合法字段。

    其他动态类型语言如何处理缺失字段？你认为 Lox 该怎么做？实现你的方案。

<!--
2.  Fields are accessed at runtime by their *string* name. But that name must
    always appear directly in the source code as an *identifier token*. A user
    program cannot imperatively build a string value and then use that as the
    name of a field. Do you think they should be able to? Devise a language
    feature that enables that and implement it.
-->
2.  字段在运行时按*字符串*名字访问。但那个名字必须始终以*标识符 token*的形式直接出现在源码里。用户程序不能命令式地拼出一个字符串值，再拿它当字段名。你认为该不该允许？设计一种支持这一点的语言特性并实现它。

<!--
3.  Conversely, Lox offers no way to *remove* a field from an instance. You can
    set a field's value to `nil`, but the entry in the hash table is still
    there. How do other languages handle this? Choose and implement a strategy
    for Lox.
-->
3.  反过来，Lox 没有办法从实例上*移除*字段。你可以把字段值设为 `nil`，但哈希表里的条目还在。其他语言怎么处理？为 Lox 选一种策略并实现。

<!--
4.  Because fields are accessed by name at runtime, working with instance state
    is slow. It's technically a constant-time operation -- thanks, hash tables
    -- but the constant factors are relatively large. This is a major component
    of why dynamic languages are slower than statically typed ones.

    How do sophisticated implementations of dynamically typed languages cope
    with and optimize this?
-->
4.  因为字段在运行时按名字访问，处理实例状态就慢。技术上这是常量时间操作——谢谢，哈希表——但常数因子相对很大。这是动态语言比静态类型语言慢的一个主要原因。

    成熟的动态类型语言实现如何应对并优化这一点？

</div>
