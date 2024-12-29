import os
import yaml
import glob
import copy
import jinja2    
import pickle
import io 

folder_template = "templates"
file_template_default = os.path.join(folder_template, "oomlout_template_part_default.md.j2")
file_template_default_absolute = os.path.join(os.path.dirname(__file__), file_template_default)

def main(**kwargs):
    
    folders_to_try = []
    folders_to_try.append("/parts")
    folders_to_try.append("/things")

    #default try
    folder = kwargs.get("folder", f"{os.path.dirname(__file__)}/parts")
    folder = folder.replace("\\","/")
    #print(f"folder: {folder}")
    ends_with_test = False
    for folder_try in folders_to_try:        
        if folder_try in folder:
            ends_with_test = True

    if not os.path.exists(folder) or not ends_with_test:
        for folder_try in folders_to_try:
            folder_test = f"{folder}{folder_try}"
            #print(f"testing folder: {folder_test}")
            if os.path.exists(folder_test):
                folder = folder_test
                break
    kwargs["folder"] = folder
    print(f"oomlout_oomp_utility_readme_generation for folder: {folder}")
    kwargs["folder_template"] = folder_template
    kwargs["file_template"] = file_template_default_absolute
    folder_template_absolute = os.path.join(os.path.dirname(__file__), folder_template)
    kwargs["folder_template_absolute"] = folder_template_absolute
    file_template_absolute = os.path.join(os.path.dirname(__file__), file_template_default)
    kwargs["file_template_absolute"] = file_template_absolute
    print(f"oomlout_oomp_utility_readme_generation for folder: {folder}")
    create_readme_recursive(**kwargs)
    
def create_readme_recursive(**kwargs):
    folder = kwargs.get("folder", os.path.dirname(__file__))
    kwargs["folder"] = folder
    folder_template_absolute = kwargs.get("folder_template_absolute", "")
    kwargs["folder_template_absolute"] = folder_template_absolute
    
    count = 0
    
    
    import threading
    semaphore = threading.Semaphore(1000)
    threads = []

    def create_thread(**kwargs):
        with semaphore:
            create_recursive_thread(**kwargs)
    folders = os.listdir(folder)
    print(f"folders: {folders}")
    for item in folders:
        #thread = threading.Thread(target=create_thread, args=(item,), kwargs=kwargs)
        kwargs["item"] = item
        thread = threading.Thread(target=create_thread, kwargs=pickle.loads(pickle.dumps(kwargs, -1)))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

cnt_readme = 0

def create_recursive_thread(**kwargs):
    item = kwargs.get("item")
    global cnt_readme
    folder = kwargs.get("folder")
    item_absolute = os.path.join(folder, item)
    
    filter = kwargs.get("filter", "")
    if filter in item:            
        if os.path.isdir(item_absolute):
            #if working.yaml exists in the folder
            if os.path.exists(os.path.join(item_absolute, "working.yaml")):
                kwargs["directory"] = item_absolute
                create_readme(**kwargs)
                cnt_readme += 1
                if cnt_readme % 100 == 0:
                    print(f".", end="")


def create_readme(**kwargs):
    directory = kwargs.get("directory", os.getcwd())    
    kwargs["directory"] = directory
    file_template = kwargs.get("file_template", file_template_default_absolute)
    kwargs["file_template"] = file_template



    generate_readme_generic(**kwargs)
    

def generate_readme_generic(**kwargs):
    import os
    directory = kwargs.get("directory",os.getcwd())    
    file_template = kwargs.get("file_template", file_template_default_absolute)
    file_output = f"{directory}/readme.md"
    details = {}

    #      yaml part
    file_yaml = f"{directory}/working.yaml"
    details = {}
    if os.path.exists(file_yaml):
        with open(file_yaml, 'r') as stream:
            try:
                details = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:   
                print(exc)
    
    #      file part
    files = []    
    #get a list of recursive files
    files = glob.glob(f"{directory}/**/*.*", recursive=True)
    #replace all \\ with /
    for i in range(len(files)):
        files[i] = files[i].replace("\\","/")
    #remove the directory from the file name
    directory = directory.replace("\\","/")
    for i in range(len(files)):
        files[i] = files[i].replace(f"{directory}/","")    
    files2 = copy.deepcopy(files)
    details["files"] = files2

    # add a markdown formated table of all values in details
    details_table = ""
    #make headers
    details_table += f"| key | value |  \n"
    details_table += f"| --- | --- |  \n"
    key_skip_list = []
    key_skip_list.append("bip_")
    key_skip_list.append("_no_")
    key_skip_list.append("_length_")
    key_skip_list.append("_capital")
    key_skip_list.append("_upper")
    key_skip_list.append("_only_numbers")
    key_skip_list.append("_first_")
    key_skip_list.append("_last_")
    key_skip_list.append("price_")
    for key in details:
        if key != "files":
            include = True
            for key_skip in key_skip_list:
                if key_skip in key:
                    include = False
            if include:
                details_table += f"| {key} | {details[key]} |  \n"
    details["table_markdown"] = details_table

    file_template = file_template
    file_output = file_output
    dict_data = details
    get_jinja2_template(file_template=file_template,file_output=file_output,dict_data=dict_data)

def get_jinja2_template(**kwargs):
    file_template = kwargs.get("file_template","")
    file_output = kwargs.get("file_output","")
    dict_data = kwargs.get("dict_data",{})

    markdown_string = ""
    #if running in windows
    if os.name == "nt":
        file_template = file_template.replace("/", "\\")
    else:
        file_template = file_template.replace("\\", "/")
    with open(file_template, "r") as infile:
        markdown_string = infile.read()
    #data2 = copy.deepcopy(dict_data)
    #use pickle to deep copy the dictionary
    data2 = pickle.loads(pickle.dumps(dict_data, -1))


    try:
        markdown_string = jinja2.Template(markdown_string).render(p=data2)
    except Exception as e:
        print(f"error in jinja2 template: {file_template}")
        print(e)
        markdown_string = f"markdown_string_error\n{e}"
    #make directory if it doesn't exist
    directory = os.path.dirname(file_output)
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    #mode = "open"
    mode = "buffer"
    
    if mode == "open":
        with open(file_output, "w", encoding="utf-8") as outfile:
            outfile.write(markdown_string)
            
    elif mode == "buffer":
        #write to a buffer then save for speen
        with io.StringIO() as outfile:
            outfile.write(markdown_string)
            with open(file_output, "w", encoding="utf-8") as outfile2:
                outfile2.write(outfile.getvalue())
                

if __name__ == '__main__':
    #folder is the path it was launched from
    
    kwargs = {}
    #folder is the command line launch path
    folder = os.getcwd()
    #folder = os.path.dirname(__file__)
    #folder = "C:/gh/oomlout_oomp_builder/parts"
    #folder = "C:/gh/oomlout_oomp_part_generation_version_1/parts"
    #folder = "Z:\\oomlout_oomp_current_version_fast_test\\parts"
    kwargs["folder"] = folder
    print(f"generating for folder: {folder}")
    main(**kwargs)