"""Centralize app object creation."""

import logging
from inspect import getsource
from hashlib import md5
from inspect import signature
from parsl.app.bash_app import BashApp
from parsl.app.python_app import PythonApp
from parsl.app.errors import InvalidAppTypeError

logger = logging.getLogger(__name__)


class AppFactory(object):
    """AppFactory streamlines creation of apps."""

    def __init__(self,
                 app_class,
                 func,
                 data_flow_kernel=None,
                 cache=False,
                 executors='all',
                 walltime=60,
                 auxiliary_files=None):
        """Construct an AppFactory for a particular app_class.

        Args:
            - app_class(Class) : An app class
            - func(Function) : The function to execute

        Kwargs:
            - data_flow_kernel(DataFlowKernel) : The DataFlowKernel which will manage app execution.
            - walltime(int) : Walltime in seconds, default=60
            - executors (str|list) : Labels of the executors that this app can execute over. Default is 'all'.
            - cache (Bool) : Enable caching of app.

        Returns:
            An AppFactory Object
        """
        self.__name__ = func.__name__
        self.app_class = app_class
        self.data_flow_kernel = data_flow_kernel
        self.func = func
        self.status = 'created'
        self.walltime = walltime
        self.executors = executors
        self.sig = signature(func)
        self.cache = cache
        self.auxiliary_files = auxiliary_files
        # Function source hashing is done here to avoid redoing this every time
        # the app is called.
        if cache is True:
            try:
                fn_source = getsource(func)
            except OSError:
                logger.debug("Unable to get source code for AppCaching. Recommend creating module")
                fn_source = func.__name__

            self.func_hash = md5(fn_source.encode('utf-8')).hexdigest()
        else:
            self.func_hash = func.__name__

    def __call__(self, *args, **kwargs):
        """Create a new object of app_class with the args, execute the app_object and return the futures.

        Args:
             Arbitrary args to the decorated function

        Kwargs:
             Arbitrary kwargs to the decorated function

        Returns:
            (App_Future, [Data_Futures...])

        The call is mostly pass through
        """
        # Create and call the new App object
        app_obj = self.app_class(self.func,
                                 data_flow_kernel=self.data_flow_kernel,
                                 executors=self.executors,
                                 walltime=self.walltime,
                                 cache=self.cache,
                                 fn_hash=self.func_hash,
                                 auxiliary_files=self.auxiliary_files)
        return app_obj(*args, **kwargs)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '<class %s"%s for %s>' % (self.app_class.__name__,
                                         self.__class__.__name__,
                                         self.__name__)


class AppFactoryFactory(object):
    """An instance AppFactoryFactory will be factory that creates object of a particular kind.

    AppFactoryFactory has the various apps registered with it, and it will return an AppFactory
    that constructs objects of a specific kind.


    """

    def __init__(self, name):
        """Constructor.

        Args:
             name(string) : Name for the appfactory

        Returns:
             object(AppFactoryFactory)
        """
        self.name = name
        self.apps = {'bash': BashApp,
                     'python': PythonApp}

    def make(self, kind, func, data_flow_kernel=None, **kwargs):
        """Creates a new App of the kind specified.

        Args:
            kind(string) : For now only(bash|python)
            data_flow_kernel(DataFlowKernel) : The DataFlowKernel which will manage app execution.
            func(Function) : The function to execute

        Kwargs:
            Walltime(int) : Walltime in seconds
            Arbritrary kwargs passed onto the AppFactory

        Raises:
            InvalidAppTypeError

        Returns:
            An AppFactory object bound to the specific app_class kind

        """
        if kind in self.apps:
            return AppFactory(self.apps[kind],
                              func,
                              data_flow_kernel=data_flow_kernel,
                              **kwargs)

        else:
            logger.error("AppFactory:%s Invalid app kind requested : %s ",
                         self.name, kind)
            raise InvalidAppTypeError(
                "AppFactory:%s Invalid app kind requested : %s ",
                self.name, kind)
