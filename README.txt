📁 WiseL (Корень проекта)
│
├── 📄 main.wise               (Исходный код на языке WiseL)
├── 📄 oniCompiler.bat         (Батник для запуска компиляции)
├── 📄 out.asm                 (Сгенерированный ассемблерный код)
└── 📄 main.exe                (Готовый исполняемый файл)
│
└── 📁 Compiler                (Папка компилятора)
    │
    ├── 📄 oniLink.py           (Главный движок: импорты, сборка, вызов FASM)
    └── 📄 oniConditions.py     (Модуль логики if/else)
│
└── 📁 Library                 (Библиотеки языка WiseL)
    │
    ├── 📄 Fluent.py            (База Fluent: хелперы, data-секция, данные виджетов)
    ├── 📄 Fluent_core.py       (Ядро Fluent: ассемблерный код отрисовки, ховера, клика)
    ├── 📄 Fluent_uix.py        (Виджеты Fluent: парсинг синтаксиса кнопок из .wise)
    ├── 📄 FluentFuncX64.py     (Функции Fluent: addFunction, onClick, hover. свойства)
    ├── 📄 WinX64.py            (Окна: парсинг окон, создание, WindowProc, сборка FASM)
    └── 📄 std.py               (Консольный модуль: print, input, pause)