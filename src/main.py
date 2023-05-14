from gunicorn.app.wsgiapp import WSGIApplication

def main():
    app = WSGIApplication()
    app.cfg.set("default_proc_name", "app")
    app.cfg.set("workers", 4)
    app.cfg.set("bind", "0.0.0.0:8000")  # adjust host and port as necessary
    app.load_wsgiapp = lambda: app  # replace my_app with your Flask app
    app.run()

if __name__ == "__main__":
    main()
