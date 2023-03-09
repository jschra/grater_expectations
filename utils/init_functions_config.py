# -- Base Python imports
import os
import logging


# -- Functions
def check_if_config_exists(project_root: str, config_name: str = "testing_config.yml"):
    """Function to check if a configuration file already exists and ensure that the user
     wants it to be overwritten, if that is the case"""
    if config_name in os.listdir(project_root):
        logging.info(
            f"A Grater Expectations configuration file ({config_name}) already exists "
            "in this directory. Are you sure you want to initialize a new file and "
            "overwrite the existing one (y/[n])?"
        )
        response = input("Input: ")
        if response.lower() in ["y", "yes"]:
            logging.info("Overwriting configuration file")
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
        project_keys = [
            "resource_group_name",
            "storage_account",
            "function_name",
            "container_registry_name",
            "docker_image_name",
            "site_name",
            "expectations_suite_name",
            "checkpoint_name",
            "run_name_template",
            "data_container_name",
        ]

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
    logging.info(f"Checking if required keys can be found in the {config_name} config")
    missing_keys = [key for key in list_keys if key not in cfg.keys()]
    if len(missing_keys) > 0:
        logging.warning(
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
        logging.warning(
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
            logging.warning(
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
