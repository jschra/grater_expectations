# -- Base Python imports
import logging
import os
import shutil
import uuid

# -- 3rd party imports
import ruamel.yaml as yaml
from jinja2 import Template


# -- Functions
def check_if_project_exists(args):
    """Function to check if the project already exists and ensure that the user wants
    it to be overwritten, if that is the case"""
    if args.name in os.listdir():
        logging.info(
            f"The project you are trying to create, {args.name}, "
            "already exists in this repository. Are you sure you want to initialize "
            "this project again and overwrite existing files (y/[n])? "
        )
        response = input("Input: ")
        if response in ["y", "Y", "yes", "Yes", "YES"]:
            logging.info(f"Overwriting existing project: {args.name}")
        else:
            raise SystemExit("Project already exists, stopping initialization")


def generate_project_files(args, provider: str, package_root: str, project_root: str):
    """Function to copy files from bootstrap files directory to project directory,
    potentially using non verbose files if passed as argument through command
    line

    Parameters
    ----------
    args:
        Command line arguments passed at runtime. Expected to contain --project/-p,
        can also contain --nonverbose/-nv
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    package_root : str
        Root directory of the package
    project_root : str
        Directory of the project
    """
    # -- 1. Copy files from bootstrap files
    from_path = os.path.join(package_root, "bootstrap_files", provider)
    to_path = os.path.join(project_root, args.name)

    copy_and_overwrite_tree(
        from_path=from_path,
        to_path=to_path,
        ignore_pattern=shutil.ignore_patterns(
            "__init__*",
            "non_verbose_files",
            "tutorial_files",
            "testing_config.yml",
            "__pycache__",
        ),
    )

    # -- 2. If nonverbose, get nonverbose files
    if args.nonverbose:
        logging.info("Replacing generated files with non-verbose versions")
        path = os.path.join(
            package_root, "bootstrap_files", provider, "non_verbose_files"
        )
        for nv_file in os.listdir(path):
            if nv_file == "__pycache__":
                continue
            orig = os.path.join(path, nv_file)
            dest = os.path.join(to_path, nv_file)
            shutil.copy2(orig, dest)


def generate_project_config(
    cfg: dict, project_root: str, args, cfg_global: dict = None
):
    """Function to copy and write project specific configurations

    Parameters
    ----------
    cfg : dict
        Project config containing required elements to generate the GE configuration
        file
    project_root : str
        Directory of the project
    args:
        Command line arguments passed at runtime. Expected to contain --project/-p
    cfg_global : dict
        Global config containing AWS account details. Are added to the configuration
        YAML if passed at runtime, otherwise they are skipped. By default, None
    """
    # -- Check for global configs, add if passed
    if cfg_global:
        cfg = {**cfg, **cfg_global}

    # -- Write file
    doc_out = yaml.dump(cfg, default_flow_style=False)
    with open(
        os.path.join(project_root, args.name, "project_config.yml"), "w"
    ) as project_yaml:
        project_yaml.write(doc_out)


def generate_ge_config(
    cfg: dict, args, provider: str, package_root: str, project_root: str
):
    """Function to generate a configuration file for Great Expectations, using arguments
    passed through a config in cfg and command line arguments in args

    Parameters
    ----------
    cfg : dict
        Project config containing required elements to generate the GE configuration
        file
    args:
        Command line arguments passed at runtime. Expected to contain a .name attribute
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    package_root : str
        Root directory of the package
    project_root : str
        Directory of the project
    """
    logging.info("Generating Great Expectations configuration file")
    path = os.path.join(project_root, args.name)
    ge_config = os.path.join(
        package_root, "docs", "templates", provider, "ge_config.yaml"
    )
    print(ge_config)
    idx = str(uuid.uuid4())

    with open(ge_config, "r") as filename:
        template = Template(filename.read())
        base_yaml = template.render(cfg=cfg, idx=idx)

    if "great_expectations" not in os.listdir(path):
        os.mkdir(os.path.join(path, "great_expectations"))

    with open(
        os.path.join(
            project_root, args.name, "great_expectations", "great_expectations.yml"
        ),
        "w",
    ) as out:
        out.write(base_yaml)


def generate_container_bash_script(
    cfg: dict,
    args,
    cfg_global: dict,
    provider: str,
    package_root: str,
    project_root: str,
):
    """Function to generate a bash script to create a docker image and push it to ECR,
    using arguments from configs in cfg and cfg_global and command line arguments in
    args

    Parameters
    ----------
    cfg : dict
        Config containing required elements to generate the GE configuration file
    args:
        Command line arguments passed at runtime. Expected to contain --project/-p
    cfg_global : dict
        Config containing required global elements (AWS account and region) to generate
        the GE configuration file
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    package_root : str
        Root directory of the package
    project_root : str
        Directory of the project
    """
    logging.info(
        "Generating bash script for making docker image and uploading it to a "
        "container registry"
    )
    if provider == "AWS":
        path = os.path.join(project_root, args.name)
        ECR_endpoint = (
            f'{cfg_global["account_id"]}.dkr.ecr.{cfg_global["region"]}.amazonaws.com'
        )
        docker_image = cfg["docker_image_name"]
        region = cfg_global["region"]
        ecr_sh = os.path.join(package_root, "docs", "templates", provider, "ecr.sh")

        with open(ecr_sh, "r") as filename:
            template = Template(filename.read())
            document = template.render(
                docker_image=docker_image, ECR_endpoint=ECR_endpoint, region=region
            )

        with open(os.path.join(path, "build_image_store_on_ecr.sh"), "w") as out:
            out.write(document)

    if provider == "Azure":
        acr_sh = os.path.join(package_root, "docs", "templates", provider, "acr.sh")
        acr_sh_ouput = os.path.join(
            project_root, args.name, "build_image_store_on_acr.sh"
        )
        with open(acr_sh, "r") as filename:
            template = Template(filename.read())
            document = template.render(cfg=cfg)
        with open(acr_sh_ouput, "w+") as filename:
            filename.write(document)


def generate_terraform_provider_config(
    args, cfg_global: dict, provider: str, package_root: str, project_root: str
):
    """Function to generate Terraform provider configuration files for each Terraform
    directory within a project

    Parameters
    ----------
    args:
        Command line arguments passed at runtime. Expected to contain the .name
        attribute
    cfg_global : dict
        Global config containing AWS account details
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    package_root : str
        Root directory of the package
    project_root : str
        Directory of the project
    """
    logging.info("Creating Terraform provider.tf configuration files")
    # -- 1. Generate document
    provider = os.path.join(package_root, "docs", "templates", provider, "provider.tf")

    with open(provider, "r") as filename:
        template = Template(filename.read())
        document = template.render(cfg_global=cfg_global)

    # -- 2. Put in all Terraform directories
    tf_dir = os.path.join(project_root, args.name, "terraform")
    loop_dirs = [path for path in os.listdir(tf_dir) if path not in [".DS_Store"]]
    for path in loop_dirs:
        with open(os.path.join(tf_dir, path, "provider.tf"), "w+") as out:
            out.write(document)


def generate_terraform_var_files(
    cfg: dict, args, cfg_global: dict, provider: str, project_root: str
):
    """Function to generate Terraform variable files that can be used in combination with
    Terraform configuration files to spin up the required AWS services

    Parameters
    ----------
    cfg : dict
        Config containing required elements to generate the GE configuration file
    args:
        Command line arguments passed at runtime. Expected to contain the .name
        attribute
    cfg_global : dict
        Global config containing AWS account details
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    project_root : str
        Directory of the project
    """
    logging.info("Creating Terraform variable configuration files")
    path = os.path.join(project_root, args.name,)

    if provider == "AWS":
        # -- 1. Generate Terraform vars for buckets
        # TODO: replace w/ template
        document_buckets = f"""ge-bucket-name      = "{cfg["store_bucket"]}"
ge-site-bucket-name = "{cfg["site_bucket"]}"
ge-data-bucket-name = "{cfg["data_bucket"]}"
        """

        # -- 2. Generate Terraform vars for lambda
        # TODO: replace w/ template
        image_uri = (
            f'"{cfg_global["account_id"]}.dkr.ecr.{cfg_global["region"]}.amazonaws.com/'
            f'{cfg["docker_image_name"]}:latest"'
        )
        document_lambda = document_buckets + f"image_uri = {image_uri}"

        # -- 3. Write files
        paths_out = []
        for target in ["buckets", "lambda"]:
            paths_out.append(
                os.path.join(
                    project_root,
                    args.name,
                    "terraform",
                    target,
                    f"{args.name}.auto.tfvars",
                )
            )

        for path, doc in zip(paths_out, [document_buckets, document_lambda]):
            with open(path, "w") as out:
                out.write(doc)

    elif provider == "Azure":
        # -- 1. Generate Terraform vars for storage
        # TODO: refactor to template
        document_storage = f"""region = "{cfg_global["region"]}"
resource_group_name = "{cfg["resource_group_name"]}"
storage_account_name = "{cfg["storage_account"]}"
data_container = "{cfg["data_container_name"]}"
"""

        # -- 2. Generate Terraform vars for function
        # TODO: refactor to template
        document_function = f"""resource_group_name = "{cfg["resource_group_name"]}"
storage_account_name = "{cfg["storage_account"]}"
app_service_name = "{cfg["function_name"]}-app-service"
function_name = "{cfg["function_name"]}-function"
docker_image_name = "{cfg["docker_image_name"]}"
container_registry_name = "{cfg["container_registry_name"]}"
"""

        # -- 3. Write files
        paths_out = []
        for target in ["storage", "function"]:
            paths_out.append(
                os.path.join(
                    project_root,
                    args.name,
                    "terraform",
                    target,
                    f"{args.name}.auto.tfvars",
                )
            )

        for path, doc in zip(paths_out, [document_storage, document_function]):
            with open(path, "w") as out:
                out.write(doc)


def copy_and_overwrite_tree(
    from_path: str, to_path: str, ignore_pattern: shutil.ignore_patterns = None
):
    """Helper function to copy files and overwrite existing ones if necessary

    Parameters
    ----------
    from_path : str
        Source path of the directory to copy
    to_path : str
        Destination path of directory to paste
    ignore_pattern : shutil.ignore_patterns, optional
        Set of patterns for files that should not be copied
    """
    logging.info(f"Copying and overwriting files from {from_path} to {to_path}")
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path, ignore=ignore_pattern)


def adjust_for_tutorial(args, provider: str, package_root: str, project_root: str):
    """Helper function to move files into tutorial directory if tutorial is being run

    Parameters
    ----------
    args:
        Command line arguments passed at runtime. Expected to contain the .name
        attribute
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    package_root : str
        Root directory of the package
    project_root : str
        Directory of the project
    """
    logging.info("Making adjustments for running the tutorial")
    if args.name == "tutorial":
        # -- 1. Add tutorial Terraform files
        path_terraform_tutorial = os.path.join(
            package_root, "bootstrap_files", provider, "tutorial_files", "terraform"
        )
        sub_directories = os.listdir(path_terraform_tutorial)
        for sub_dir in sub_directories:
            # -- .1 Set originating subdir
            orig = os.path.join(path_terraform_tutorial, sub_dir)

            # -- .2 Construct target subdir
            dest = os.path.join(project_root, args.name, "terraform", sub_dir)

            # -- .3 Copy file
            for tutorial_file in os.listdir(orig):
                shutil.copy2(
                    os.path.join(orig, tutorial_file), os.path.join(dest, tutorial_file)
                )

        # # -- 2. Add tutorial data
        orig = os.path.join(package_root, "bootstrap_files", "tutorial_data")
        dest = os.path.join(project_root, args.name, "data")
        copy_and_overwrite_tree(orig, dest)

        # -- 3. Copy tutorial notebook and remove expectation_suite.ipynb
        orig = os.path.join(
            package_root,
            "bootstrap_files",
            provider,
            "tutorial_files",
            "tutorial_notebook.ipynb",
        )

        dest = os.path.join(project_root, args.name, "tutorial_notebook.ipynb")
        shutil.copy2(orig, dest)
        os.remove(os.path.join(project_root, args.name, "expectation_suite.ipynb"))

        # # -- 4. Replace lambda function or Azure function directory
        function_mapping = {"AWS": "lambda_function.py", "Azure": "function"}
        orig = os.path.join(
            package_root,
            "bootstrap_files",
            provider,
            "tutorial_files",
            function_mapping[provider],
        )
        dest = os.path.join(project_root, args.name, function_mapping[provider])

        if provider == "AWS":
            shutil.copy2(orig, dest)
        elif provider == "Azure":
            copy_and_overwrite_tree(orig, dest)


def start_notebook(args, project_root: str, notebook_name: str = "expectation_suite"):
    """Helper function to open up the expectation_suite.ipynb notebook upon
    initialization of a new project"""
    logging.info(f"Opening {notebook_name} notebook for project {args.name}")
    path = os.path.join(project_root, args.name, f"{notebook_name}.ipynb")
    print(path)
    os.system(f'nbopen "{path}"')
