var myCodeMirror;
var doc;
var bConverted = false;

function codemirror_run(_doc) {

    var themes = ['3024-day',
'3024-night',
'ambiance-mobile',
'ambiance',
'base16-dark',
'base16-light',
'blackboard',
'cobalt',
'eclipse',
'elegant',
'erlang-dark',
'lesser-dark',
'mbo',
'midnight',
'monokai',
'neat',
'night',
'paraiso-dark',
'paraiso-light',
'pastel-on-dark',
'rubyblue',
'solarized',
'the-matrix',
'tomorrow-night-eighties',
'twilight',
'vibrant-ink',
'xq-dark',
'xq-light'];

    var langs = ['apl',
'asterisk',
'clike',
'clojure',
'cobol',
'coffeescript',
'commonlisp',
'css',
'd',
'diff',
'dtd',
'ecl',
'eiffel',
'erlang',
'fortran',
'gas',
'gfm',
'gherkin',
'go',
'groovy',
'haml',
'haskell',
'haxe',
'htmlembedded',
'htmlmixed',
'http',
'jade',
'javascript',
'jinja2',
'julia',
'less',
'livescript',
'lua',
'markdown',
'mirc',
'mllike',
'nginx',
'ntriples',
'octave',
'pascal',
'pegjs',
'perl',
'php',
'pig',
'properties',
'python',
'q',
'r',
'rpm',
'rst',
'ruby',
'rust',
'sass',
'scheme',
'shell',
'sieve',
'smalltalk',
'smarty',
'smartymixed',
'sparql',
'sql',
'stex',
'tcl',
'tiddlywiki',
'tiki',
'toml',
'turtle',
'vb',
'vbscript',
'velocity',
'verilog',
'xml',
'xquery',
'yaml',
'z80'];


    theme_sel = document.createElement("SELECT");
    theme_sel.setAttribute("onchange", "enable_codemirror();selectTheme(this)");

    for (var i=0; i<themes.length; i++) {
        var opt = document.createElement("OPTION");
        opt.text = themes[i];
        opt.value = themes[i];
        theme_sel.appendChild(opt);
    }


    lang_sel = document.createElement("SELECT");
    lang_sel.setAttribute("onchange", "enable_codemirror();selectMode(this)");

    for (var i=0; i<langs.length; i++) {
        var opt = document.createElement("OPTION");
        opt.text = langs[i];
        opt.value = langs[i];
        lang_sel.appendChild(opt);
    }

    doc = _doc;
    var editorObj = _doc.getElementById('editor-textarea');
    //editorObj.insertBefore(opt);
    editorObj.nextSibling.appendChild(theme_sel);
    editorObj.nextSibling.appendChild(lang_sel);

    enable_codemirror();
    // myCodeMirror.setOption("mode", 'tiki');
    // myCodeMirror.setOption("theme", 'solarized');
}

function enable_codemirror() {

    if (bConverted) return;

    var editorObj = doc.getElementById('editor-textarea');
    // editorObj.style.width = '100%';
    myCodeMirror = CodeMirror.fromTextArea(
                                editorObj,
                                {
                                    mode:'tiki',
                                    theme:'solarized',
                                    lineNumbers:true,
                                    lineWrapping:true,
                                    onKeyEvent: function(i, e) {
                                      // Hook into F11
                                      if ((e.keyCode == 122 || e.keyCode == 27) && e.type == 'keydown') {
                                        e.stop();
                                        return toggleFullscreenEditing();
                                      }
                                    },
                                }
    );
    // myCodeMirror.setHeight(500);
    myCodeMirror.setSize('100%', 500);
    bConverted = true;
}

function selectTheme(node) {
    var theme = node.options[node.selectedIndex].innerHTML;
    myCodeMirror.setOption("theme", theme);
}

function selectMode(node) {
    var mode = node.options[node.selectedIndex].innerHTML;
    myCodeMirror.setOption("mode", mode);
}


function toggleFullscreenEditing()
{
    var editorDiv = $('.CodeMirror-scroll');
    if (!editorDiv.hasClass('fullscreen')) {
        toggleFullscreenEditing.beforeFullscreen = { height: editorDiv.height(), width: editorDiv.width() }
        editorDiv.addClass('fullscreen');
        editorDiv.height('100%');
        editorDiv.width('100%');
        editor.refresh();
    }
    else {
        editorDiv.removeClass('fullscreen');
        editorDiv.height(toggleFullscreenEditing.beforeFullscreen.height);
        editorDiv.width(toggleFullscreenEditing.beforeFullscreen.width);
        editor.refresh();
    }
}


