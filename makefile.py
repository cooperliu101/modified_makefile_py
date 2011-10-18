'''
*** SHED SKIN Python-to-C++ Compiler ***
Copyright 2005-2011 Mark Dufour; License GNU GPL version 3 (See LICENSE)

makefile.py: generate makefile

'''

import sys
from distutils import sysconfig

from shared import *

def generate_makefile():
    if sys.platform == 'win32':
        pyver = '%d%d' % sys.version_info[:2]
        prefix = sysconfig.get_config_var('prefix').replace('\\', '/')
    else:
        pyver = sysconfig.get_config_var('VERSION') or sysconfig.get_python_version()
        includes = '-I' + sysconfig.get_python_inc() + ' '
        if not getgx().pypy:
            includes += '-I' + sysconfig.get_python_inc(plat_specific=True)

        if sys.platform == 'darwin':
            ldflags = sysconfig.get_config_var('BASECFLAGS')
        else:
            ldflags = (sysconfig.get_config_var('LIBS') or '') + ' '
            ldflags += (sysconfig.get_config_var('SYSLIBS') or '') + ' '
            if not getgx().pypy:
                ldflags += '-lpython'+pyver
                if not sysconfig.get_config_var('Py_ENABLE_SHARED'):
                    ldflags += ' -L' + sysconfig.get_config_var('LIBPL')

    ident = getgx().main_module.ident
    if getgx().extension_module:
        if sys.platform == 'win32': ident += '.pyd'
        else: ident += '.so'

    makefile = file(getgx().makefile_name, 'w')

    libdir = getgx().libdir.replace(' ','\ ')
    print >>makefile, 'SHEDSKIN_LIBDIR=%s' % (libdir)
    filenames = []
    mods = getgx().modules.values()
    for mod in mods:
        filename = mod.filename[:-3] # strip .py
        filename = filename.replace(' ','\ ') # make paths valid
        filename = filename.replace(libdir,'${SHEDSKIN_LIBDIR}')
        filenames.append(filename)

    cppfiles = [fn+'.cpp' for fn in filenames]
    hppfiles = [fn+'.hpp' for fn in filenames]
    for always in ('re',):
        repath = connect_paths('${SHEDSKIN_LIBDIR}', always)
        if not repath in filenames:
            cppfiles.append(repath+'.cpp')
            hppfiles.append(repath+'.hpp')

    cppfiles.sort(reverse=True)
    hppfiles.sort(reverse=True)
    cppfiles = ' \\\n\t'.join(cppfiles)
    hppfiles = ' \\\n\t'.join(hppfiles)

    # import flags
    if getgx().flags: flags = getgx().flags
    elif os.path.isfile('FLAGS'): flags = 'FLAGS'
    elif getgx().msvc: flags = connect_paths(getgx().sysdir, 'FLAGS.msvc')
    elif sys.platform == 'win32': flags = connect_paths(getgx().sysdir, 'FLAGS.mingw')
    elif sys.platform == 'darwin': flags = connect_paths(getgx().sysdir, 'FLAGS.osx')
    else: flags = connect_paths(getgx().sysdir, 'FLAGS')

    for line in file(flags):
        line = line[:-1]

        variable = line[:line.find('=')].strip()
        if variable == 'CCFLAGS':
            line += ' -I. -I${SHEDSKIN_LIBDIR}'
            if sys.platform == 'darwin' and os.path.isdir('/usr/local/include'):
                line += ' -I/usr/local/include' # XXX
            if sys.platform == 'darwin' and os.path.isdir('/opt/local/include'):
                line += ' -I/opt/local/include' # XXX
            if not getgx().wrap_around_check: line += ' -D__SS_NOWRAP'
            if not getgx().bounds_checking: line += ' -D__SS_NOBOUNDS'
            if getgx().fast_random: line += ' -D__SS_FASTRANDOM'
            if not getgx().assertions: line += ' -D__SS_NOASSERT'
            if getgx().fast_hash: line += ' -D__SS_FASTHASH'
            if getgx().longlong: line += ' -D__SS_LONG'
            if getgx().backtrace: line += ' -D__SS_BACKTRACE -rdynamic -fno-inline'
            if getgx().pypy: line += ' -D__SS_PYPY'
            if getgx().extension_module:
                if getgx().msvc: line += ' /DLL /LIBPATH:%s/libs /LIBPATH:python%s' % (prefix, pyver)
                elif sys.platform == 'win32': line += ' -I%s/include -D__SS_BIND' % prefix
                else: line += ' -g -fPIC -D__SS_BIND ' + includes

        elif variable == 'LFLAGS':
            if sys.platform == 'darwin' and os.path.isdir('/opt/local/lib'): # XXX
                line += ' -L/opt/local/lib'
            if sys.platform == 'darwin' and os.path.isdir('/usr/local/lib'): # XXX
                line += ' -L/usr/local/lib'
            if getgx().extension_module:
                if sys.platform == 'win32': line += ' -shared -L%s/libs -lpython%s' % (prefix, pyver)
                elif sys.platform == 'darwin': line += ' -bundle -undefined dynamic_lookup ' + ldflags
                elif sys.platform == 'sunos5': line += ' -shared -Xlinker ' + ldflags
                else: line += ' -shared -Xlinker -export-dynamic ' + ldflags

            if 'socket' in [m.ident for m in mods]:
                if sys.platform == 'win32':
                    line += ' -lws2_32'
                elif sys.platform == 'sunos5':
                    line += ' -lsocket -lnsl'
            if 'os' in [m.ident for m in mods]:
                if sys.platform not in ['win32', 'darwin', 'sunos5']:
                    line += ' -lutil'
            if 'hashlib' in [m.ident for m in mods]:
                line += ' -lssl'

        print >>makefile, line
    print >>makefile

    print >>makefile, 'CPPFILES=%s\n' % cppfiles
    print >>makefile, 'HPPFILES=%s\n' % hppfiles

    print >>makefile, 'all:\t'+ident+'\n'

    # executable (normal, debug, profile) or extension module
    _out = '-o '
    _ext=''
    if getgx().msvc:
        _out = '/out:'
        _ext = ''
        if not getgx().extension_module:
            _ext = '.exe'
    targets = [('', '')]
    if not getgx().extension_module:
        targets += [('_prof', '-pg -ggdb'), ('_debug', '-g -ggdb')]
    for suffix, options in targets:
        print >>makefile, ident+suffix+':\t$(CPPFILES) $(HPPFILES)'
        print >>makefile, '\t$(CC) '+options+' $(CCFLAGS) $(CPPFILES) $(LFLAGS) '+_out+ident+suffix+_ext + '\n'

    # clean
    ext = ''
    if sys.platform == 'win32' and not getgx().extension_module:
        ext = '.exe'
    print >>makefile, 'clean:'
    targets = [ident+ext]
    if not getgx().extension_module:
        targets += [ident+'_prof'+ext, ident+'_debug'+ext]
    print >>makefile, '\trm -f %s\n' % ' '.join(targets)

    # phony
    print >>makefile, '.PHONY: all clean\n'
    makefile.close()
