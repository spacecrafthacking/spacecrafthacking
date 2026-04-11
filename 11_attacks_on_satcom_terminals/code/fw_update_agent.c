#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>

#define LISTEN_PORT 9000
#define BUF_SIZE 1024
#define DOWNLOAD_PATH "/tmp/update.bin"

// Trim trailing newline/carriage returns
static void trim_newline(char *s) {
    size_t len = strlen(s);
    while (len > 0 && (s[len-1] == '\n' || s[len-1] == '\r')) {
        s[len-1] = '\0';
        len--;
    }
}

// Blocking read of one line (terminated by '\n'), up to BUF_SIZE-1
static ssize_t recv_line(int fd, char *buf, size_t maxlen) {
    size_t i = 0;
    while (i < maxlen - 1) {
        char c;
        ssize_t n = recv(fd, &c, 1, 0);
        if (n <= 0) {
            return n;
        }
        buf[i++] = c;
        if (c == '\n')
            break;
    }
    buf[i] = '\0';
    return (ssize_t)i;
}

// Run a shell command and return its exit status
static int run_cmd(const char *cmd) {
    int status = system(cmd);
    if (status == -1) {
        return -1;
    }
    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }
    return -1;
}

// Download update via wget
static int download_update(const char *url) {
    char cmd[BUF_SIZE * 2];
    snprintf(cmd, sizeof(cmd),
             "wget -q -O %s '%s'",
             DOWNLOAD_PATH, url);
    return run_cmd(cmd);
}

// Make downloaded file executable
static int make_executable(void) {
    char cmd[BUF_SIZE];
    snprintf(cmd, sizeof(cmd), "chmod +x %s", DOWNLOAD_PATH);
    return run_cmd(cmd);
}

// Execute downloaded binary (blocking)
static int execute_update(void) {
    pid_t pid = fork();
    if (pid < 0) {
        return -1;
    }
    if (pid == 0) {
        // Child: exec the binary
        execl(DOWNLOAD_PATH, DOWNLOAD_PATH, (char *)NULL);
        _exit(127);
    }
    // Parent: wait for child
    int status;
    if (waitpid(pid, &status, 0) < 0) {
        return -1;
    }
    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }
    return -1;
}

static void handle_client(int client_fd) {
    char buf[BUF_SIZE];

    // Simple protocol: "UPDATE <url>\n"
    ssize_t n = recv_line(client_fd, buf, sizeof(buf));
    if (n <= 0) {
        return;
    }
    trim_newline(buf);

    if (strncmp(buf, "UPDATE ", 7) != 0) {
        const char *resp = "ERR Unknown command\n";
        send(client_fd, resp, strlen(resp), 0);
        return;
    }

    const char *url = buf + 7;
    if (strlen(url) == 0) {
        const char *resp = "ERR No URL\n";
        send(client_fd, resp, strlen(resp), 0);
        return;
    }

    const char *resp_downloading = "OK Downloading\n";
    send(client_fd, resp_downloading, strlen(resp_downloading), 0);

    if (download_update(url) != 0) {
        const char *resp = "ERR Download failed\n";
        send(client_fd, resp, strlen(resp), 0);
        return;
    }

    if (make_executable() != 0) {
        const char *resp = "ERR chmod failed\n";
        send(client_fd, resp, strlen(resp), 0);
        return;
    }

    const char *resp_executing = "OK Executing\n";
    send(client_fd, resp_executing, strlen(resp_executing), 0);

    int rc = execute_update();
    char resp_final[BUF_SIZE];
    snprintf(resp_final, sizeof(resp_final),
             "OK ExitCode %d\n", rc);
    send(client_fd, resp_final, strlen(resp_final), 0);
}

int main(void) {
    int sockfd;
    struct sockaddr_in servaddr;

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("socket");
        return 1;
    }

    int opt = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = htonl(INADDR_ANY);
    servaddr.sin_port = htons(LISTEN_PORT);

    if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind");
        close(sockfd);
        return 1;
    }

    if (listen(sockfd, 5) < 0) {
        perror("listen");
        close(sockfd);
        return 1;
    }

    printf("fw_update_agent: listening on port %d\n", LISTEN_PORT);

    for (;;) {
        struct sockaddr_in cliaddr;
        socklen_t len = sizeof(cliaddr);
        int client_fd = accept(sockfd, (struct sockaddr *)&cliaddr, &len);
        if (client_fd < 0) {
            perror("accept");
            continue;
        }

        handle_client(client_fd);
        close(client_fd);
    }

    close(sockfd);
    return 0;
}

