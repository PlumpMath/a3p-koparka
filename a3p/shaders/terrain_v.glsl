//GLSL
#version 140
in vec4 p3d_Vertex;
in vec3 p3d_Normal;

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat4 p3d_ModelMatrix;

out vec2 terrain_uv;
out vec4 world_pos;;


void main()
    {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;      
          
    world_pos=p3d_ModelMatrix* p3d_Vertex;         
    terrain_uv=(world_pos.xy+vec2(256.0, 256.0))*0.001953125;// *(1/512)
    }
