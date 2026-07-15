import reapy


def main() -> None:
    reapy.connect()
    project = reapy.Project()
    print("reaper_connection=ok")
    print(f"project_name={project.name}")
    print(f"project_path={project.path}")


if __name__ == "__main__":
    main()
