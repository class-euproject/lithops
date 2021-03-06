# PyWren runtime for IBM Cloud Functions

PyWren main runtime is responsible to execute Python functions within IBM Cloud Functions cluster. The strong requirement here is to match Python versions between the client and the runtime. The runtime may also contain additional packages which your code depends on.

PyWren for IBM Cloud is shipped with these default runtimes:

| Runtime name | Python version | Packages included |
| ----| ----| ---- |
| ibmfunctions/pywren:3.5 | 3.5 | [list of packages](https://github.com/ibm-functions/runtime-python/blob/master/python3.6/CHANGELOG.md) |
| ibmfunctions/action-python-v3.6 | 3.6 | [list of packages](https://github.com/ibm-functions/runtime-python/blob/master/python3.6/CHANGELOG.md) |
| ibmfunctions/action-python-v3.7 | 3.7 | [list of packages](https://github.com/ibm-functions/runtime-python/blob/master/python3.7/CHANGELOG.md) |

The default runtime is created the first time you execute a function. PyWren automatically detects the Python version of your environment and deploys the default runtime based on it.

Alternatively, you can create the default runtime by running the following command:
    
    $ pywren-runtime create default

To run a function with the default runtime you don't need to specify anything in the code since all is internally managed by PyWren:
```python
import pywren_ibm_cloud as pywren

def my_function(x):
    return x + 7

pw = pywren.ibm_cf_executor()
pw.call_async(my_function, 3)
result = pw.get_result()
```

If you need some Python modules (or other system libraries) which are not included in the default docker images (see table above), it is possible to build your own PyWren runtime with all of them.

1. **Build your own PyWren runtime**

    This alternative usage is based on to build a local Docker image, deploy it to the docker hub (you need a [Docker Hub account](https://hub.docker.com)) and use it as a PyWren base runtime.
    Project provides the skeleton of the Docker image:
    
    * [Dockerfile](Dockerfile) - The image is based on `python:3.6-slim-jessie`. 
    
    To build your own runtime, first install the Docker CE version in your client machine. You can find the instructions [here](https://docs.docker.com/install/). If you already have Docker installed omit this step.
    
    Login to your Docker hub account by running in a terminal the next command.
    
    	docker login
    
    Navigate to `runtime` and update the Dockerfile with your required packages and Python modules.
    If you need another Python version, for example Python 3.5, you must use the [Dockerfile.python35](Dockerfile.python35) that
    points to a source image based on Python 3.5. Finally run the build script:
    
        $ pywren-runtime build docker_username/runtimename:tag
    
    Note that Docker hub image names look like *"docker_username/runtimename:tag"* and must be all lower case, for example:
    
       $ pywren-runtime build jsampe/pywren-custom-runtime:3.5
    
    Once you have built your runtime with all of your necessary packages, now you are able to use it with PyWren.
    To do so you have to specify the full docker image name when you create the *ibm_cf_executor* instance, for example:
    ```python
    import pywren_ibm_cloud as pywren
    
    def my_function(x):
        return x + 7
    
    pw = pywren.ibm_cf_executor(runtime='jsampe/pywren-custom-runtime:3.5')
    pw.call_async(my_function, 3)
    result = pw.get_result()
    ```
    
    *NOTE: In this previous example we built a Docker image based on Python 3.5, this means that now we also need Python 3.5 in the client machine.*
    
    In order to use a self-built docker image as a runtime for PyWren, you have to login to your [Docker Hub account](https://hub.docker.com) and ensure that the image is **public**.


Maybe someone already built a Docker image with all the packages you need, and put it in a public repository.
In this case you can use that Docker image and avoid the building process.

2. **Use an already built runtime from a public repository**

    To create a PyWren runtime based on already built Docker image, execute the following command which will create all the necessary information to use the runtime with your PyWren.
    
        $ pywren-runtime create docker_username/runtimename:tag
      
    For example, you can use an already created runtime based on Python 3.5 and with the *matplotlib* and *nltk* libraries by running:
    
        $ pywren-runtime create jsampe/pw-mpl-nltk:3.5
        
    Once finished, you can use the runtime in your PyWren code:
    ```python
    import pywren_ibm_cloud as pywren
    
    def my_function(x):
        return x + 7
    
    pw = pywren.ibm_cf_executor(runtime='jsampe/pw-mpl-nltk:3.5')
    pw.call_async(my_function, 3)
    result = pw.get_result()
    ```

If you are a developer, and you modified the PyWeen source code, you need to deploy the changes before executing PyWren.

3. **Update an existing runtime**

    You can update default runtime by:
    	
    	$ pywren-runtime update default
    
    You can update any other runtime deployed in your namespace by specifying the docker image that the runtime depends on:
    
       $ pywren-runtime update docker_username/runtimename:tag
      
    For example, you can update an already created runtime based on the Docker image `jsampe/pw-mpl-nltk:3.5` by:
    
       $ pywren-runtime update jsampe/pw-mpl-nltk:3.5



You can also delete existing runtimes in your namespace.

4. **Delete an existing runtime**

    You can delete default runtime by:
    	
    	$ pywren-runtime delete default
    
    You can delete any other runtime deployed in your namespace by specifying the docker image that the runtime depends on:
    
       $ pywren-runtime delete docker_username/runtimename:tag
      
    For example, you can delete runtime based on the Docker image `jsampe/pw-mpl-nltk:3.5` by:
    
       $ pywren-runtime delete jsampe/pw-mpl-nltk:3.5
        