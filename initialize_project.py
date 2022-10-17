from version import __version__
from argparse import ArgumentParser
from jinja2 import Template
import os
import shutil
import ruamel.yaml as yaml
import uuid
import logging


# Constants
PACKAGE_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(".")
CONFIGS_FILE = "testing_config.yml"
SUPPORTED_PROVIDERS = ["AWS", "Azure"]

# Logger
logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main_program():
    # -- 1. Parse arguments passed at runtime from terminal
    parser = initialize_parser()
    args = parser.parse_args()
    logger.info("Parsing command line arguments")

    if args.create == "config":
        if args.provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                "The selected provider is currently not supported by Grater "
                "Expectations. Please select one from the following options: "
                f"{SUPPORTED_PROVIDERS}"
            )

        logger.info(f"Selected provider is: {args.provider}")
        logger.info(
            f"Creating configuration file testing_config.yml for {args.provider} in "
            "current directory"
        )

        _ = check_if_config_exists(PROJECT_ROOT)
        src = os.path.join(PACKAGE_ROOT, "bootstrap_files", args.provider, CONFIGS_FILE)
        dst = os.path.join(PROJECT_ROOT, CONFIGS_FILE)
        shutil.copy(src, dst)

        logger.info(
            "Config file created. Please save project relevant configurations in testing_config.yml and run grater create project"
        )

    # -- 2. Load and check configurations
    if args.create == "project":

        logger.info("Loading configurations from testing_config.yml")

        with open(os.path.join(PROJECT_ROOT, CONFIGS_FILE)) as cfg_yaml:
            # -- Load
            cfg_all = yaml.safe_load(cfg_yaml)
            cfg_global = cfg_all["global"]
            provider = cfg_global["provider"]

            try:
                cfg = cfg_all[args.name]
            except KeyError as ke:
                logger.warning(
                    f"The project configurations for {args.name} were not found in the"
                    " testing_config.yml. Please add it."
                )
                raise ke

            # -- Check global config
            global_keys = {
                "AWS": ["account_id", "region", "provider"],
                "Azure": ["provider",],
            }

            evaluate_global_config(cfg_global, global_keys[provider], "global")

            # -- Check project config
            project_keys = get_config_project_keys(provider)
            evaluate_config_keys(cfg, project_keys, args.name)

        # -- 3. Check if the project exists and if so, if the user wants to continue. Then,
        # Create directory if needed
        _ = check_if_project_exists(args)
        if args.name not in os.listdir():
            os.mkdir(args.name)

        # -- 4. Copy bootstrap files (do this before copying any other files, as it
        #       might overwrite and remove previously copied files)
        generate_project_files(args, provider)

        # -- 5. Copy configuration
        generate_project_config(cfg, args, cfg_global)

        # -- 6. Generate Great Expectations config yml
        generate_ge_config(cfg, args, provider)

        # -- 7. Generate bash script for building Docker image and push to container
        #       registry
        generate_container_bash_script(cfg, args, cfg_global, provider)

        # -- 8. Generate Terraform var files
        generate_terraform_var_files(cfg, args, cfg_global, provider)

        # # -- 9. Add provider.tf in each Terraform directory
        generate_terraform_provider_config(args, cfg_global, provider)

        # -- 10. If tutorial, overwrite files with tutorial equivalents and add
        #       tutorial data
        adjust_for_tutorial(args, provider)

        # # -- 11. Start testing suite notebook
        if args.name == "tutorial":
            start_notebook(args, "tutorial_notebook")
        else:
            start_notebook(args)


# Functions
def initialize_parser() -> ArgumentParser:
    """Function to initialize command line parser for the package

    Returns
    -------
    ArgumentParser
        An initialize argument parser
    """
    # -- 1. Create new parser, add (sub-)arguments
    parser = ArgumentParser(description="CLI for Grater Expectations")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    subparsers = parser.add_subparsers()

    # -- .1 Add create subparser
    create = subparsers.add_parser(
        "create", help="command to create configs and projects"
    )
    create_subparsers = create.add_subparsers(dest="create")

    # -- .2 Add config to create subparser
    create_cnf = create_subparsers.add_parser("config", help="command to create config")
    create_cnf.add_argument(
        "-p",
        "--provider",
        metavar="",
        type=str,
        required=True,
        help="Cloud provider to initialize config for",
    )

    # -- .3 Add project to create subparser
    create_prj = create_subparsers.add_parser(
        "project", help="command to create projects"
    )
    create_prj.add_argument(
        "-n", "--name", type=str, required=True, help="name of the project", metavar=""
    )
    create_prj.add_argument(
        "-nv", "--nonverbose", action="store_true", help="option for non-verbose files"
    )

    return parser


def check_if_config_exists(project_root: str, config_name: str = "testing_config.yml"):
    """Function to check if a configuration file already exists and ensure that the user
     wants it to be overwritten, if that is the case"""
    if config_name in os.listdir(project_root):
        logger.info(
            f"A Grater Expectations configuration file ({config_name}) already exists "
            "in this directory. Are you sure you want to initialize a new file and "
            "overwrite the existing one (y/[n])?"
        )
        response = input("Input: ")
        if response in ["y", "Y", "yes", "Yes", "YES"]:
            logger.info(f"Overwriting configuration file")
        else:
            raise SystemExit("Configuration file already exists, stopping creation")


def get_config_project_keys(provider: str) -> list:
    """Function that returns a list of expected keys in a project configuration,
    depending on the selected provider

    Parameters
    ----------
    provider : str
        Selected cloud provider that Grater Expectations should be configured for

    Returns
    -------
    list
        A list of expected keys in the project config
    """
    if provider == "AWS":
        project_keys = [
            "store_bucket",
            "store_bucket_prefix",
            "site_bucket",
            "site_bucket_prefix",
            "docker_image_name",
            "site_name",
            "expectations_suite_name",
            "checkpoint_name",
            "run_name_template",
            "data_bucket",
            "prefix_data",
        ]
    elif provider == "Azure":
        project_keys = []

    return project_keys


def evaluate_config_keys(cfg: dict, list_keys: list, config_name: str):
    """Function to evaluate if the passed configurations contain the required keys to
    bootstrap a new GE project

    Parameters
    ----------
    cfg : dict
        The passed config to be evaluated
    list_keys : list
        The list of keys the config should contain
    config_name : str
        The name of the config passed, used to make potential errors more understandable

    Raises
    ------
    KeyError
        A KeyError is raised if the configuration does not contain all required keys
    """
    # -- 1. Check for missing keys
    logger.info(f"Checking if required keys can be found in the {config_name} config")
    missing_keys = [key for key in list_keys if key not in cfg.keys()]
    if len(missing_keys) > 0:
        logger.warning(
            f"Not all keys found in the {config_name} config. Missing: {missing_keys}"
        )
        raise KeyError(
            f"The {config_name} configuration is missing the "
            f"following arguments: {missing_keys}"
        )

    # -- 2. Check for missing values
    DEFAULT = "MUST_BE_SET"
    missing_values = [key for key, value in cfg.items() if value == DEFAULT]
    if len(missing_values) > 0:
        logger.warning(
            f"Not all keys found in the {config_name} config have been configured. "
            f"Not configured: {missing_values}"
        )
        raise KeyError(
            f"The {config_name} configuration is missing values for the "
            f"following arguments: {missing_values}"
        )

    pass


def evaluate_global_config(cfg: dict, list_keys: list, config_name: str):
    """Function to evaluate if the passed global configuration contains the required 
    keys to and has proper values set for its parameters to bootstrap a new GE project

    Parameters
    ----------
    cfg : dict
        The passed config to be evaluated
    list_keys : list
        The list of keys the config should contain
    config_name : str
        The name of the config passed, used to make potential errors more understandable

    Raises
    ------
    KeyError
        A KeyError is raised if the configuration does not contain all required keys
    """
    # -- 1. Check for presence of keys
    evaluate_config_keys(cfg, list_keys, config_name)

    # -- 2. Check if default values have been adjusted
    DEFAULT = "MUST_BE_SET"
    failed = False
    list_failed = []
    for key in list_keys:
        if cfg[key] == DEFAULT:
            list_failed.append(key)
            logger.warning(
                f"The value for {key} in the global config is set to its default value."
                " Please fill in a proper value for this parameter."
            )
            failed = True

    if failed:
        raise ValueError(
            "Parameters were found in the global config that are still set to their "
            "default values. Please enter proper values for these parameters. The "
            f"values that must be set are for: {list_failed}"
        )
    else:
        pass


def check_if_project_exists(args):
    """Function to check if the project already exists and ensure that the user wants
    it to be overwritten, if that is the case"""
    if args.name in os.listdir():
        logger.info(
            f"The project you are trying to create, {args.name}, "
            "already exists in this repository. Are you sure you want to initialize "
            "this project again and overwrite existing files (y/[n])? "
        )
        response = input("Input: ")
        if response in ["y", "Y", "yes", "Yes", "YES"]:
            logger.info(f"Overwriting existing project: {args.name}")
        else:
            raise SystemExit("Project already exists, stopping initialization")


def generate_project_files(args, provider: str):
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
    """
    # -- 1. Copy files from bootstrap files
    from_path = os.path.join(PACKAGE_ROOT, "bootstrap_files", provider)
    to_path = os.path.join(PROJECT_ROOT, args.name)

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
        logger.info("Replacing generated files with non-verbose versions")
        path = os.path.join(
            PACKAGE_ROOT, "bootstrap_files", provider, "non_verbose_files"
        )
        for nv_file in os.listdir(path):
            if nv_file == "__pycache__":
                continue
            orig = os.path.join(path, nv_file)
            dest = os.path.join(to_path, nv_file)
            shutil.copy2(orig, dest)


def generate_project_config(cfg: dict, args, cfg_global: dict = None):
    """Function to copy and write project specific configurations

    Parameters
    ----------
    cfg : dict
        Project config containing required elements to generate the GE configuration file
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
        os.path.join(PROJECT_ROOT, args.name, "project_config.yml"), "w"
    ) as project_yaml:
        project_yaml.write(doc_out)


def generate_ge_config(cfg: dict, args, provider: str):
    """Function to generate a configuration file for Great Expectations, using arguments
    passed through a config in cfg and command line arguments in args

    Parameters
    ----------
    cfg : dict
        Project config containing required elements to generate the GE configuration file
    args:
        Command line arguments passed at runtime. Expected to contain a .name attribute
    provider : str
        Selected cloud provider that Grater Expectations should be configured for
    """
    logger.info("Generating Great Expectations configuration file")
    path = os.path.join(PROJECT_ROOT, args.name)
    ge_config = os.path.join(
        PACKAGE_ROOT, "docs", "templates", provider, "ge_config.yaml"
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
            PROJECT_ROOT, args.name, "great_expectations", "great_expectations.yml"
        ),
        "w",
    ) as out:
        out.write(base_yaml)


def generate_container_bash_script(cfg: dict, args, cfg_global: dict, provider: str):
    """Function to generate a bash script to create a docker image and push it to ECR,
    using arguments from configs in cfg and cfg_global and command line arguments in args

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
    """
    logger.info(
        "Generating bash script for making docker image and uploading it to a "
        "container registry"
    )
    if provider == "AWS":
        path = os.path.join(PROJECT_ROOT, args.name)
        ECR_endpoint = (
            f'{cfg_global["account_id"]}.dkr.ecr.{cfg_global["region"]}.amazonaws.com'
        )
        docker_image = cfg["docker_image_name"]
        region = cfg_global["region"]
        ecr_sh = os.path.join(PACKAGE_ROOT, "docs", "templates", provider, "ecr.sh")

        with open(ecr_sh, "r") as filename:
            template = Template(filename.read())
            document = template.render(
                docker_image=docker_image, ECR_endpoint=ECR_endpoint, region=region
            )

        with open(
            os.path.join(PROJECT_ROOT, args.name, "build_image_store_on_ecr.sh"), "w"
        ) as out:
            out.write(document)

    if provider == "Azure":
        acr_sh = os.path.join(PACKAGE_ROOT, "docs", "templates", provider, "acr.sh")
        acr_sh_ouput = os.path.join(
            PROJECT_ROOT, args.name, "build_image_store_on_acr.sh"
        )
        with open(acr_sh, "r") as filename:
            template = Template(filename.read())
            document = template.render(cfg=cfg)
        with open(acr_sh_ouput, "w+") as filename:
            filename.write(document)


def generate_terraform_provider_config(args, cfg_global: dict, provider: str):
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
    """
    logger.info("Creating Terraform provider.tf configuration files")
    # -- 1. Generate document
    provider = os.path.join(PACKAGE_ROOT, "docs", "templates", provider, "provider.tf")

    with open(provider, "r") as filename:
        template = Template(filename.read())
        document = template.render(cfg_global=cfg_global)

    # -- 2. Put in all Terraform directories
    tf_dir = os.path.join(PROJECT_ROOT, args.name, "terraform")
    loop_dirs = [path for path in os.listdir(tf_dir) if path not in [".DS_Store"]]
    for path in loop_dirs:
        with open(os.path.join(tf_dir, path, "provider.tf"), "w+") as out:
            out.write(document)


def generate_terraform_var_files(cfg: dict, args, cfg_global: dict, provider: str):
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
    """
    logger.info("Creating Terraform variable configuration files")
    path = os.path.join(PROJECT_ROOT, args.name,)

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
                    PROJECT_ROOT,
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
                    PROJECT_ROOT,
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
    logger.info(f"Copying and overwriting files from {from_path} to {to_path}")
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path, ignore=ignore_pattern)


def adjust_for_tutorial(args, provider: str):
    """Helper function to move files into tutorial directory if tutorial is being run"""
    logger.info("Making adjustments for running the tutorial")
    if args.name == "tutorial":
        # -- 1. Add tutorial Terraform files
        path_terraform_tutorial = os.path.join(
            PACKAGE_ROOT, "bootstrap_files", provider, "tutorial_files", "terraform"
        )
        sub_directories = os.listdir(path_terraform_tutorial)
        for sub_dir in sub_directories:
            # -- .1 Set originating subdir
            orig = os.path.join(path_terraform_tutorial, sub_dir)

            # -- .2 Construct target subdir
            dest = os.path.join(PROJECT_ROOT, args.name, "terraform", sub_dir)

            # -- .3 Copy file
            for tutorial_file in os.listdir(orig):
                shutil.copy2(
                    os.path.join(orig, tutorial_file), os.path.join(dest, tutorial_file)
                )

        # # -- 2. Add tutorial data
        orig = os.path.join(PACKAGE_ROOT, "bootstrap_files", "tutorial_data")
        dest = os.path.join(PROJECT_ROOT, args.name, "data")
        copy_and_overwrite_tree(orig, dest)

        # -- 3. Copy tutorial notebook and remove expectation_suite.ipynb
        orig = os.path.join(
            PACKAGE_ROOT,
            "bootstrap_files",
            provider,
            "tutorial_files",
            "tutorial_notebook.ipynb",
        )

        dest = os.path.join(PROJECT_ROOT, args.name, "tutorial_notebook.ipynb")
        shutil.copy2(orig, dest)
        os.remove(os.path.join(PROJECT_ROOT, args.name, "expectation_suite.ipynb"))

        # # -- 4. Replace lambda function or Azure function directory
        function_mapping = {"AWS": "lambda_function.py", "Azure": "function"}
        orig = os.path.join(
            PACKAGE_ROOT,
            "bootstrap_files",
            provider,
            "tutorial_files",
            function_mapping[provider],
        )
        dest = os.path.join(PROJECT_ROOT, args.name, function_mapping[provider])

        if provider == "AWS":
            shutil.copy2(orig, dest)
        elif provider == "Azure":
            copy_and_overwrite_tree(orig, dest)
            

def start_notebook(args, notebook_name: str = "expectation_suite"):
    """Helper function to open up the expectation_suite.ipynb notebook upon
    initialization of a new project"""
    logger.info(f"Opening {notebook_name} notebook for project {args.name}")
    path = os.path.join(PROJECT_ROOT, args.name, f"{notebook_name}.ipynb")
    print(path)
    os.system(f'nbopen "{path}"')


if __name__ == "__main__":
    main_program()
