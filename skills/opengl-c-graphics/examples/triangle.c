/*
 * triangle.c — minimal, C-correct modern OpenGL (3.3 core) in plain C.
 *
 * Demonstrates the canonical setup -> compile -> link -> draw sequence from
 * LearnOpenGL, written to the standards of the c-systems-engineer skill:
 *   - GL handles use GL types (GLuint/GLint/GLsizei/GLchar), never bare int.
 *   - Every shader compile and program link is status-checked; the info log is
 *     sized from GL_INFO_LOG_LENGTH and heap-allocated, never truncated into a
 *     fixed 512-byte buffer.
 *   - Every GL object created has a matching delete on every exit path.
 *   - A KHR_debug callback is installed when the context advertises it.
 *
 * Build (macOS, Homebrew):
 *   cc -std=c11 -Wall -Wextra -Wpedantic triangle.c glad.c \
 *      -I include $(pkg-config --cflags --libs glfw3) -framework OpenGL -o triangle
 * Build (Linux):
 *   cc -std=c11 -Wall -Wextra -Wpedantic triangle.c glad.c \
 *      $(pkg-config --cflags --libs glfw3) -ldl -o triangle
 *
 * glad.c / include/glad/glad.h come from https://glad.dav1d.de (gl 3.3 core).
 */
#include <glad/glad.h>   /* MUST be included before GLFW */
#include <GLFW/glfw3.h>
#include <stdio.h>
#include <stdlib.h>

static const char *VERT_SRC =
    "#version 330 core\n"
    "layout (location = 0) in vec3 aPos;\n"
    "void main() { gl_Position = vec4(aPos, 1.0); }\n";

static const char *FRAG_SRC =
    "#version 330 core\n"
    "out vec4 FragColor;\n"
    "void main() { FragColor = vec4(1.0, 0.5, 0.2, 1.0); }\n";

/* APIENTRY matches the GLDEBUGPROC calling convention. Per OpenGL Insights
 * Ch.33: calling ANY GL or window-system function from inside this callback is
 * undefined behaviour, so this body does I/O only. */
static void APIENTRY gl_debug_cb(GLenum source, GLenum type, GLuint id,
                                 GLenum severity, GLsizei length,
                                 const GLchar *message, const void *user)
{
    (void)source; (void)type; (void)id; (void)length; (void)user;
    if (severity == GL_DEBUG_SEVERITY_NOTIFICATION) return;
    fprintf(stderr, "[GL] %s\n", message);
}

/* Compile one shader stage. Returns 0 on failure (0 is never a valid name). */
static GLuint compile_shader(GLenum stage, const char *src)
{
    GLuint sh = glCreateShader(stage);
    if (sh == 0) return 0;
    glShaderSource(sh, 1, &src, NULL);
    glCompileShader(sh);

    GLint ok = GL_FALSE;
    glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (ok != GL_TRUE) {
        GLint len = 0;
        glGetShaderiv(sh, GL_INFO_LOG_LENGTH, &len);   /* includes the NUL */
        char *log = (len > 0) ? malloc((size_t)len) : NULL;
        if (log) {
            glGetShaderInfoLog(sh, len, NULL, log);
            fprintf(stderr, "shader compile failed:\n%s\n", log);
            free(log);
        }
        glDeleteShader(sh);
        return 0;
    }
    return sh;
}

/* Link a program from two stages. Detaches+deletes the stages either way;
 * returns 0 on failure. Caller still owns vs/fs handles only until this call. */
static GLuint link_program(GLuint vs, GLuint fs)
{
    GLuint prog = glCreateProgram();
    if (prog == 0) {
        glDeleteShader(vs);
        glDeleteShader(fs);
        return 0;
    }
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glLinkProgram(prog);

    /* The stage objects are not needed past link. Detaching drops the program's
     * reference; combined with glDeleteShader the GL frees them. Do this before
     * the status branch so both paths release the stages exactly once. */
    glDetachShader(prog, vs);
    glDetachShader(prog, fs);
    glDeleteShader(vs);
    glDeleteShader(fs);

    GLint ok = GL_FALSE;
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (ok != GL_TRUE) {
        GLint len = 0;
        glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &len);   /* query before delete */
        char *log = (len > 0) ? malloc((size_t)len) : NULL;
        if (log) {
            glGetProgramInfoLog(prog, len, NULL, log);
            fprintf(stderr, "program link failed:\n%s\n", log);
            free(log);
        }
        glDeleteProgram(prog);
        return 0;
    }
    return prog;
}

static void framebuffer_size_cb(GLFWwindow *w, int width, int height)
{
    (void)w;
    glViewport(0, 0, width, height);
}

int main(void)
{
    if (!glfwInit()) {
        fprintf(stderr, "glfwInit failed\n");
        return EXIT_FAILURE;
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_DEBUG_CONTEXT, GLFW_TRUE);   /* enable GL debug */
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);  /* required on macOS */
#endif

    GLFWwindow *win = glfwCreateWindow(800, 600, "triangle", NULL, NULL);
    if (!win) {
        fprintf(stderr, "glfwCreateWindow failed\n");
        glfwTerminate();
        return EXIT_FAILURE;
    }
    glfwMakeContextCurrent(win);
    glfwSetFramebufferSizeCallback(win, framebuffer_size_cb);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        fprintf(stderr, "glad failed to load GL\n");
        glfwDestroyWindow(win);
        glfwTerminate();
        return EXIT_FAILURE;
    }

    /* Install debug output if the loaded context supports it (4.3 / KHR_debug). */
    GLint flags = 0;
    glGetIntegerv(GL_CONTEXT_FLAGS, &flags);
    if ((flags & GL_CONTEXT_FLAG_DEBUG_BIT) && glDebugMessageCallback) {
        glEnable(GL_DEBUG_OUTPUT);
        glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);   /* fire on the offending call */
        glDebugMessageCallback(gl_debug_cb, NULL);
    }

    GLuint vs = compile_shader(GL_VERTEX_SHADER, VERT_SRC);
    GLuint fs = compile_shader(GL_FRAGMENT_SHADER, FRAG_SRC);
    GLuint prog = 0;
    if (vs && fs) {
        prog = link_program(vs, fs);   /* takes ownership of vs and fs */
    } else {
        /* link_program was not called, so we still own whatever compiled. */
        if (vs) glDeleteShader(vs);
        if (fs) glDeleteShader(fs);
    }
    if (prog == 0) {
        glfwDestroyWindow(win);
        glfwTerminate();
        return EXIT_FAILURE;
    }

    const GLfloat verts[] = {
        -0.5f, -0.5f, 0.0f,
         0.5f, -0.5f, 0.0f,
         0.0f,  0.5f, 0.0f,
    };

    GLuint vao = 0, vbo = 0;
    glGenVertexArrays(1, &vao);
    glGenBuffers(1, &vbo);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof verts, verts, GL_STATIC_DRAW);
    /* index 0, 3 floats, not normalized, tight stride, zero offset. The final
     * arg is a byte offset cast to a pointer — a GL API wart, not a real ptr. */
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                          3 * sizeof(GLfloat), (const void *)0);
    glEnableVertexAttribArray(0);
    glBindVertexArray(0);

    while (!glfwWindowShouldClose(win)) {
        if (glfwGetKey(win, GLFW_KEY_ESCAPE) == GLFW_PRESS)
            glfwSetWindowShouldClose(win, GLFW_TRUE);

        glClearColor(0.1f, 0.1f, 0.12f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        glUseProgram(prog);
        glBindVertexArray(vao);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        glfwSwapBuffers(win);
        glfwPollEvents();
    }

    glDeleteVertexArrays(1, &vao);
    glDeleteBuffers(1, &vbo);
    glDeleteProgram(prog);
    glfwDestroyWindow(win);
    glfwTerminate();
    return EXIT_SUCCESS;
}
