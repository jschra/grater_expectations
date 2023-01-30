# -- Base Python imports
import os
import shutil
import logging

# -- 3rd party imports
import ruamel.yaml as yaml

# -- Internal module imports
from utils.init_parser import initialize_parser
from utils.init_functions_config import (
    check_if_config_exists,
    get_config_project_keys,
    evaluate_config_keys,
    evaluate_global_config,
)
from utils.init_functions_aws import validate_s3_buckets, validate_region
from utils.init_functions_project import (
    check_if_project_exists,
    generate_project_files,
    generate_project_config,
    generate_ge_config,
    generate_container_bash_script,
    generate_terraform_provider_config,
    generate_terraform_var_files,
    adjust_for_tutorial,
    start_notebook,
)

# -- Constants
CONFIGS_FILE = "testing_config.yml"
SUPPORTED_PROVIDERS = ["AWS", "Azure"]
PACKAGE_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(".")

# -- Logger
logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# -- Main program
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
            "Config file created. Please save project relevant configurations in "
            "testing_config.yml and run grater create project"
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
                "Azure": ["provider", "region"],
            }

            evaluate_global_config(cfg_global, global_keys[provider], "global")

            # -- Check project config
            project_keys = get_config_project_keys(provider)
            evaluate_config_keys(cfg, project_keys, args.name)

            # -- Apply provider specific checks of config inputs
            if provider == "AWS":
                validate_region(cfg_global["region"])
                validate_s3_buckets(cfg)

        # -- 3. Check if the project exists and if so, if the user wants to continue.
        # Then, create directory if needed
        _ = check_if_project_exists(args)
        if args.name not in os.listdir():
            os.mkdir(args.name)

        # -- 4. Copy bootstrap files (do this before copying any other files, as it
        #       might overwrite and remove previously copied files)
        generate_project_files(args, provider, PACKAGE_ROOT, PROJECT_ROOT)

        # -- 5. Copy configuration
        generate_project_config(cfg, PROJECT_ROOT, args, cfg_global)

        # -- 6. Generate Great Expectations config yml
        generate_ge_config(cfg, args, provider, PACKAGE_ROOT, PROJECT_ROOT)

        # -- 7. Generate bash script for building Docker image and push to container
        #       registry
        generate_container_bash_script(
            cfg, args, cfg_global, provider, PACKAGE_ROOT, PROJECT_ROOT
        )

        # -- 8. Generate Terraform var files
        generate_terraform_var_files(cfg, args, cfg_global, provider, PROJECT_ROOT)

        # # -- 9. Add provider.tf in each Terraform directory
        generate_terraform_provider_config(
            args, cfg_global, provider, PACKAGE_ROOT, PROJECT_ROOT
        )

        # -- 10. If tutorial, overwrite files with tutorial equivalents and add
        #       tutorial data
        adjust_for_tutorial(args, provider, PACKAGE_ROOT, PROJECT_ROOT)

        # # -- 11. Start testing suite notebook
        if args.name == "tutorial":
            start_notebook(args, PROJECT_ROOT, "tutorial_notebook")
        else:
            start_notebook(args, PROJECT_ROOT)


if __name__ == "__main__":
    main_program()
