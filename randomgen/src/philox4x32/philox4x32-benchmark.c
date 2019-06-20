// #include "Random123/philox.h"
#include <inttypes.h>
#include <stdio.h>
#include <time.h>

#define PHILOX_M4x32_0 ((uint32_t)0xD2511F53)
#define PHILOX_M4x32_1 ((uint32_t)0xCD9E8D57)
#define PHILOX_W32_0 ((uint32_t)0x9E3779B9)
#define PHILOX_W32_1 ((uint32_t)0xBB67AE85)
#define PHILOX4x32_DEFAULT_ROUNDS 10

#if defined(__GNUC__) || defined(__clang__)
#define FORCE_INLINE(decl) decl __attribute__((always_inline))
#else
#define FORCE_INLINE(decl) __forceinline decl
#endif

struct r123array1x32 { uint32_t v[1]; };                                              
struct r123array2x32 { uint32_t v[2]; };                                              
struct r123array4x32 { uint32_t v[4]; };                                              

static __inline uint32_t mulhilo32(uint32_t a, uint32_t b, uint32_t* hip){ 
    uint64_t product = ((uint64_t)a)*((uint64_t)b);                              
    *hip = product>>32;                                                  
    return (uint32_t)product;                                               
}

static __inline FORCE_INLINE(struct r123array4x32 _philox4x32round(struct r123array4x32 ctr, struct r123array2x32 key)); 
static __inline struct r123array4x32 _philox4x32round(struct r123array4x32 ctr, struct r123array2x32 key){ 
    uint32_t hi0;                                                          
    uint32_t hi1;                                                          
    uint32_t lo0 = mulhilo32(PHILOX_M4x32_0, ctr.v[0], &hi0);              
    uint32_t lo1 = mulhilo32(PHILOX_M4x32_1, ctr.v[2], &hi1);              
    struct r123array4x32 out = {{hi1^ctr.v[1]^key.v[0], lo1,               
                              hi0^ctr.v[3]^key.v[1], lo0}};             
    return out;                                                         
}


static __inline struct r123array2x32 _philox4x32bumpkey( struct r123array2x32 key) { 
    key.v[0] += PHILOX_W32_0;                                        
    key.v[1] += PHILOX_W32_1;                                        
    return key;                                                      
}

enum r123_enum_philox4x32 { philox4x32_rounds = PHILOX4x32_DEFAULT_ROUNDS }; 
typedef struct r123array4x32 philox4x32_ctr_t;                  
typedef struct r123array2x32 philox4x32_key_t;              
typedef struct r123array2x32 philox4x32_ukey_t;              
static __inline philox4x32_key_t philox4x32keyinit(philox4x32_ukey_t uk) { return uk; } 
static __inline FORCE_INLINE(philox4x32_ctr_t philox4x32_R(unsigned int R, philox4x32_ctr_t ctr, philox4x32_key_t key)); 
static __inline philox4x32_ctr_t philox4x32_R(unsigned int R, philox4x32_ctr_t ctr, philox4x32_key_t key) { 
    if(R>0){                                       ctr = _philox4x32round(ctr, key); } 
    if(R>1){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>2){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>3){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>4){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>5){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>6){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>7){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>8){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>9){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>10){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>11){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>12){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>13){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>14){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    if(R>15){ key = _philox4x32bumpkey(key); ctr = _philox4x32round(ctr, key); } 
    return ctr;                                                         
}
         
#define philox4x32(c,k) philox4x32_R(philox4x32_rounds, c, k)

#define N 1000000000
int main() {
  philox4x32_ctr_t ctr = {{0, 0, 0, 0}};
  philox4x32_key_t key = {{0, 0xDEADBEAF}};
  philox4x32_ctr_t out;
  uint64_t count = 0, sum = 0;
  int i, j;
  clock_t begin = clock();
  for (i = 0; i < N / 4UL; i++) {
    ctr.v[0]++;
    out = philox4x32(ctr, key);
#if !defined(__clang__) || !defined(__GNUC__)
    #pragma loop(no_vector)
#endif
    for (j = 0; j < 4; j++) {
      sum += out.v[j];
      count++;
    }
  }
  clock_t end = clock();
  double time_spent = (double)(end - begin) / CLOCKS_PER_SEC;
  printf("%0.10f seconds\n", time_spent);
  printf("sum: 0x%" PRIx64 "\ncount: %" PRIu64 "\n", sum, count);
  printf("%" PRIu64 " randoms per second\n",
         (uint64_t)((N / time_spent) / 1000000 * 1000000));
}
