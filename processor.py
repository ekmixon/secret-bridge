from os.path import isfile
import logging
import tempfile
import subprocess

class EventProcessor:
    def __init__(self):
        self.client = None
        self.detectors = []
        self.notifiers = []
        self.repo_cache = {}
        # TODO: should this live here? maybe better handled
        # by its own class
        self.findings = {}

    def configure_client(self, client):
        self.client = client

    def configure_detectors(self, detectors):
        self.detectors = detectors

    def configure_notifiers(self, notifiers):
        self.notifiers = notifiers

    def _get_html_url(self, event, commit_payload):
        return f"{event.repo.html_url}/commit/{commit_payload['sha']}"

    def _clone_and_establish_baseline(self, event):
        repo_url = event.repo.clone_url
        repo_full_name = event.repo.full_name
        if repo_url not in self.repo_cache:
            repo_dir = tempfile.TemporaryDirectory(event.repo.name)
            logging.info(f'Cloning repository {repo_full_name} into {repo_dir.name}')
            subprocess.run(["git", "clone", repo_url, repo_dir.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.repo_cache[repo_url] = repo_dir
            # we haven't cloned this repository yet, so we don't have a baseline
            logging.info(f'Establishing baseline for {repo_full_name}')
            self.findings[repo_url] = {}
            for detector in self.detectors:
                self.findings[repo_url][detector.name] = set(detector.run(repo_dir.name, None, event.repo.html_url))
                if len(self.findings[repo_url][detector.name]) != 0:
                    for notifier in self.notifiers:
                        notifier.process(self.findings[repo_url][detector.name], detector.name)
                # TODO: report these findings
        else:
            # TODO: maybe pull out of else for clarity
            repo_dir = self.repo_cache[repo_url]
        return repo_dir


    def process_event(self, event):
        repo_dir = self._clone_and_establish_baseline(event)
        repo_url = event.repo.clone_url
        repo_full_name = event.repo.full_name
        commit_cache = {}
        for commit_payload in event.payload['commits']:
            logging.info(f'Pulling latest copy of {repo_full_name}')
            subprocess.run(["git", "checkout", "master"], cwd=repo_dir.name, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["git", "pull"], cwd=repo_dir.name, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            commit_sha = commit_payload['sha']
            # this may fail, since GitHub event history may not reflect
            # Git repository history. TODO?
            # currently all detectors will still run, and repo-aware detectors
            # will run on the `master`
            try:
                subprocess.run(["git", "checkout", commit_sha], cwd=repo_dir.name,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError:
                logging.info(
                    f"Unable to check out commit {commit_sha} (no longer reflected in current repo?)"
                )

                continue

            if commit_sha not in commit_cache:
                commit_cache[commit_sha] = event.repo.get_commit(commit_sha)
            commit = commit_cache[commit_sha]
            for file in commit.files:
                if not isfile(file.filename):
                    continue

                logging.info(
                    f'PushEvent {event.id} included commit {commit.sha} which modified file {file.filename}'
                )

                new_commit_findings = {}
                for detector in self.detectors:
                    detector_findings = detector.run(repo_dir.name, file, self._get_html_url(event, commit_payload))
                    new_detector_findings = set(detector_findings) - self.findings[repo_url][detector.name]
                    new_commit_findings[detector.name] = new_detector_findings
                    self.findings[repo_url][detector.name] |= new_detector_findings
                for detector_name, value in new_commit_findings.items():
                    if len(value) != 0:
                        for notifier in self.notifiers:
                            notifier.process(new_commit_findings[detector_name], detector_name)


Processor = EventProcessor()
