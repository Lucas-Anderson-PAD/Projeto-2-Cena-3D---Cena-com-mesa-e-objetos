// Blinn-Phong por fragmento, em espaco "world", com luz de spot, segunda luz
// pontual, plano de corte (discard + tampa nas faces de tras) e fog linear.
// Grupos: 0=global, 1=matrix, 2=material, 3=texturas.

struct Global {
  projection: mat4x4<f32>,
  camera_position: vec4<f32>,
  light_ambient: vec3<f32>,
  light_diffuse: vec3<f32>,
  light_specular: vec3<f32>,
  light_position: vec4<f32>,
  light_direction: vec3<f32>,
  light_cos_inner: f32,
  light_cos_outer: f32,
  light2_position: vec4<f32>,
  light2_diffuse: vec3<f32>,
  light2_specular: vec3<f32>,
  fog_color: vec3<f32>,
  fog_near: f32,
  fog_far: f32,
  fog_enabled: f32,
  clip_plane: vec4<f32>,
  clip_plane_color: vec4<f32>,
}

struct Matrix {
  vertex: mat4x4<f32>,
  normal: mat4x4<f32>,
}

struct Material {
  base_color: vec3<f32>,
  opacity: f32,
  specular_color: vec3<f32>,
  shininess: f32,
}

@group(0) @binding(0) var<uniform> global: Global;
@group(1) @binding(0) var<storage, read> matrix: array<Matrix>;
@group(2) @binding(0) var<uniform> material: Material;
@group(3) @binding(0) var decal_texture: texture_2d<f32>;
@group(3) @binding(1) var decal_sampler: sampler;

struct VsOut {
  @builtin(position) position: vec4<f32>,
  @location(0) world_pos: vec3<f32>,
  @location(1) world_normal: vec3<f32>,
  @location(2) uv: vec2<f32>,
}

@vertex
fn vs_main(@builtin(instance_index) inst: u32,
           @location(0) coord: vec3<f32>,
           @location(1) normal: vec3<f32>,
           @location(2) tangent: vec3<f32>,
           @location(3) texcoord: vec2<f32>) -> VsOut {
  let m = matrix[inst];
  let wp = m.vertex * vec4<f32>(coord, 1.0);
  var out: VsOut;
  out.position = global.projection * wp;
  out.world_pos = wp.xyz;
  out.world_normal = (m.normal * vec4<f32>(normal, 0.0)).xyz;
  out.uv = texcoord;
  return out;
}

@fragment
fn fs_main(fin: VsOut, @builtin(front_facing) front: bool) -> @location(0) vec4<f32> {
  let p = fin.world_pos;

  // amostragem antes de qualquer discard (fluxo uniforme)
  let decal = textureSample(decal_texture, decal_sampler, fin.uv).rgb;

  // plano de corte: descarta o lado negativo
  if (dot(global.clip_plane, vec4<f32>(p, 1.0)) < 0.0) {
    discard;
  }

  let n = normalize(fin.world_normal);
  let base = material.base_color * decal;
  let v = normalize(global.camera_position.xyz - p);

  // luz 1: spot
  let l = normalize(global.light_position.xyz - p);
  let cos_angle = dot(-l, normalize(global.light_direction));
  let spot = smoothstep(global.light_cos_outer, global.light_cos_inner, cos_angle);
  let ndl = max(dot(n, l), 0.0);
  let h = normalize(l + v);
  var specular = vec3<f32>(0.0);
  if (ndl > 0.0) {
    specular = global.light_specular * material.specular_color
             * pow(max(dot(n, h), 0.0), material.shininess) * spot;
  }
  var color = global.light_ambient * base
            + global.light_diffuse * base * ndl * spot
            + specular;

  // luz 2: pontual
  let l2 = normalize(global.light2_position.xyz - p);
  let ndl2 = max(dot(n, l2), 0.0);
  let h2 = normalize(l2 + v);
  var specular2 = vec3<f32>(0.0);
  if (ndl2 > 0.0) {
    specular2 = global.light2_specular * material.specular_color
              * pow(max(dot(n, h2), 0.0), material.shininess);
  }
  color = color + global.light2_diffuse * base * ndl2 + specular2;

  // tampa do corte: face de tras visivel pelo corte
  if (!front) {
    color = global.clip_plane_color.rgb;
  }

  // fog linear
  if (global.fog_enabled > 0.5) {
    let d = distance(global.camera_position.xyz, p);
    let f = clamp((global.fog_far - d) / (global.fog_far - global.fog_near), 0.0, 1.0);
    color = mix(global.fog_color, color, f);
  }
  return vec4<f32>(color, material.opacity);
}
