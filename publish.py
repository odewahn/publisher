from argparse import ArgumentParser, BooleanOptionalAction
import os
import time
from rich.console import Console
from rich.table import Table
from rich import print
import requests as request
from ftplib import FTP
from dotenv import dotenv_values
from pathlib import Path
import os
from shlex import split as shlex_split
import paramiko


VERSION = "0.0.1"
config = {}
ENV_FILENAME = ".publisher"


console = Console()

# *****************************************************************************************
# Useful functions
# *****************************************************************************************


def load_config():
    # Load the required environment variables from the config file in ~/.publisher
    # And then merge with the environment variables from the system
    # This allows the user to override the config file with environment variables
    # This is useful for CI/CD pipelines
    out = {}
    home = str(Path.home())
    out = dotenv_values(home + "/" + ENV_FILENAME)
    out = dict(out)  # Convert OrderedDict to an actual dictionary
    return {**out, **os.environ}


def get_sftp_client():
    transport = paramiko.Transport((config["FTP_HOST"], 22))
    transport.connect(username=config["FTP_USER"], password=config["FTP_PASSWORD"])
    sftp = paramiko.SFTPClient.from_transport(transport)
    return sftp


# *****************************************************************************************
# Implment functions that do the actual work
# *****************************************************************************************
def print_portal_link(work):
    msg = f"https://cowbird.platform.gcp.oreilly.review/admin/portal/safariportalsubmission/?q={work}"
    console.log("To view logs: " + msg)


def monitor(work):
    # Every 20 seconds read the files in the current directory
    # Once all the files end in ".processed", exit the loop
    # FTP into the site
    sftp = get_sftp_client()
    with console.status("[bold green]Monitoring ingestions for " + work) as status:
        while True:
            files = sftp.listdir(".")
            if len(files) == 0:
                print("No files found for this work")
                break
            # in a single line, check if all files end in processed, exit
            if all(f.endswith(".processed") for f in files):
                print("Ingestion complete")
                break
            time.sleep(10)
    print_portal_link(work)


def df():
    print(f"Connecting to {config['FTP_HOST']} as {config['FTP_USER']}")

    transport = paramiko.Transport((config["FTP_HOST"], 22))
    transport.connect(username=config["FTP_USER"], password=config["FTP_PASSWORD"])
    sftp = paramiko.SFTPClient.from_transport(transport)

    files = sftp.listdir(".")
    print(files)
    sftp.put("/Users/odewahn/Desktop/publisher/requirements.txt", "requirements.txt")
    sftp.close()


def ingest(work, path):
    if path is None:
        console.log("Path is not set.  Use --path to set the path to the work.")
        exit()

    path = os.path.expanduser(path)
    print(f"Ingesting from {path}")

    files = [f for f in os.listdir(path) if f.startswith(work)]
    files = [os.path.abspath(path + "/" + f) for f in files]

    if len(files) < 4:
        print("The following files are the minimum required to ingest a work:")
        table = Table(show_header=True)
        table.add_column("Filename")
        table.add_column("Title")
        table.add_row(
            work + ".{epub | mp4 | mp3}", "The epub, video, or audio file(s) to ingest"
        )
        table.add_row(work + ".xml", "An xml file definining the work's metadata")
        table.add_row(work + ".< png | jpg >", "A cover image for the work")
        print(table)

    # Move the file that ends with .xml to the end of the list
    # This is because the ingestion process works best if the xml file is the last file processed
    files = sorted(files, key=lambda x: x.endswith(".xml"))
    # the xml file is at the end.  Now sort the other files by their filename
    files = sorted(files[:-1]) + files[-1:]

    if args.dryrun:
        print("The following files will be uploaded:")
        for f in files:
            print(f)

    # FTP into the site
    sftp = get_sftp_client()

    # Upload the files that match the work to the ftp host
    for f in files:
        console.log(f"Uploading: {os.path.abspath(f)} => {os.path.basename(f)}")
        sftp.put(
            os.path.abspath(f),
            os.path.basename(f),
        )

    print_portal_link(work)


def build(work, path, project, branch):
    # if the ATLAS_API_KY is not set, exit
    if config["ATLAS_API_KEY"] is None:
        raise Exception("ATLAS_API_KEY is not set")

    if path is None:
        raise Exception("Path is not set.  Use --path to set the path to the work.")

    if project is None:
        raise Exception(
            "Project is not set. Use --project to set the project to build."
        )

    if branch is None:
        raise Exception("Branch is not set. Use --branch to set the branch to build.")

    build = {"status": "pending", "download_url": None, "message": None}
    initial_submission = {}  # Define a variable to hold the response from the API
    msg = f"[bold green]Building {branch} branch of {project}"

    # Make the initial build request
    with console.status(msg):
        initial_submission = request.post(
            "https://atlas.oreilly.com/api/builds",
            data={
                "project": project,
                "branch": branch,
                "auth_token": config["ATLAS_API_KEY"],
                "formats": "epub",
            },
        )
        # Exit if there is an error in the request
        if initial_submission.status_code != 200:
            console.log(initial_submission.json())
            exit()
        build = initial_submission.json()["status"][0]

    # Monitor the buikd request until it completes or fails
    with console.status(msg):
        while True:
            res = request.get(
                "https://atlas.oreilly.com" + initial_submission.json()["build_url"],
                params={"auth_token": config["ATLAS_API_KEY"]},
            )
            if res.status_code != 200:
                print(res.json())
                exit()

            build = res.json()["status"][0]
            console.log(build)

            # If the build is complete, break out of the loop
            if build["status"] in ["complete", "failed"]:
                console.log("Build complete or failed")
                break

            # If the build is not complete, wait 2 seconds and try again
            time.sleep(2)

    # If the build failed, exit
    if build["status"] == "failed":
        console.log(build["message"])
        exit()

    with console.status(f"[bold green]Downloading the zip file to {path}"):
        r = request.get(build["download_url"], allow_redirects=True)
        # Exit if there is an error
        if r.status_code != 200:
            console.log(r.json())
            exit()
        open(path + work + ".epub", "wb").write(r.content)


# *****************************************************************************************
# Process commandline arguments
# *****************************************************************************************


def define_args(argString=None):

    ACTIONS = ["build", "ingest", "monitor", "version", "df"]

    parser = ArgumentParser(description="Publish a file to ingestion pipeline")
    parser.add_argument("action", choices=ACTIONS, help="The action to perform ")
    parser.add_argument("--work", help="The work identifier", required=False)
    parser.add_argument("--path", help="Local file path", required=False, default="./")
    parser.add_argument("--project", help="Atlas project to build", required=False)
    parser.add_argument(
        "--dryrun",
        help="Only show files that will be uploaded during ingestion",
        required=False,
        default=False,
        action=BooleanOptionalAction,
    )
    parser.add_argument(
        "--branch",
        help="Atlas branch to build [default:main]",
        default="main",
    )

    if argString:
        return parser.parse_args(shlex_split(argString))
    else:
        return parser.parse_args()


def process_command():

    if args.action == "version":
        print(f"Version: {VERSION}")
        return

    if args.action == "monitor":
        monitor(args.work)
        return

    if args.action == "ingest":
        ingest(args.work, args.path)
        return

    if args.action == "build":
        download_url = build(args.work, args.path, args.project, args.branch)
        if download_url is not None:
            download_and_unzip_build(args.work, args.path, download_url)
        return

    if args.action == "df":
        df()
        return


if __name__ == "__main__":
    config = load_config()
    args = define_args()
    process_command()
