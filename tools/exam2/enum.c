/* 2학년 16과목의 일자(목0 금1 월2 화3) 분할 전수 탐색.
   절대 제약(일자 수준): A·P 화요일 불가, 하루 4과목 금지(화는 3과목 금지), 하루 0과목 금지,
   화요일 슬롯 ≤ 4, 그 외 요일 슬롯 ≤ MAXSLOT. 슬롯 = 과목 수 - 같은 날 동시시행 쌍(O+J, N+P).
   allow=1이면 인원 1명인 조합 하나에 한해 위반 허용(도움반 학생이 그 조합일 가능성 보고용). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define NS 16
#define NC 84
int mask[NC], cnt[NC], nmax[NC]; char cname[NC][9];
int load[4][NC];
int day[NS];
int cap[4] = {3,3,3,2};
int allow = 0, MAXSLOT = 7;
int viol = -1;              /* 위반 허용된 조합 인덱스 */
long long leaves = 0, nodes = 0;
int sub_combos[NS][NC], nsc[NS];
FILE *out;
const int O_=14, J_=9, N_=13, P_=15, A_=0;

void leaf(void){
    int n[4]={0,0,0,0};
    for(int s=0;s<NS;s++) n[day[s]]++;
    int slots[4]; for(int d=0;d<4;d++) slots[d]=n[d];
    if(day[O_]==day[J_]) slots[day[O_]]--;
    if(day[N_]==day[P_]) slots[day[N_]]--;
    if(slots[3]>4) return;
    for(int d=0;d<3;d++) if(slots[d]>MAXSLOT) return;
    /* 하루 0과목 검사 */
    int v = viol;
    for(int c=0;c<NC;c++){
        for(int d=0;d<4;d++) if(load[d][c]==0){
            if(allow && cnt[c]==1 && (v==-1 || v==c)) { v=c; }
            else return;
        }
    }
    leaves++;
    for(int s=0;s<NS;s++) fputc('0'+day[s], out);
    fprintf(out," %d\n", v);
}

void dfs(int s){
    nodes++;
    if(s==NS){ leaf(); return; }
    for(int d=0;d<4;d++){
        if(d==3 && (s==A_ || s==P_)) continue;
        int saved_viol = viol, ok=1;
        /* 적용 */
        for(int i=0;i<nsc[s];i++){
            int c=sub_combos[s][i];
            load[d][c]++;
            if(load[d][c]>cap[d] && nmax[c]>0){
                if(allow && cnt[c]==1 && nmax[c]==1 && (viol==-1 || viol==c)) viol=c;
                else ok=0;
            }
        }
        if(ok){
            day[s]=d; dfs(s+1);
        }
        for(int i=0;i<nsc[s];i++) load[d][sub_combos[s][i]]--;
        viol = saved_viol;
    }
}

int main(int argc, char**argv){
    if(argc>1) allow=atoi(argv[1]);
    if(argc>2) MAXSLOT=atoi(argv[2]);
    const char* outname = argc>3? argv[3] : "parts.txt";
    FILE* f=fopen("combos.txt","r");
    for(int c=0;c<NC;c++){ if(fscanf(f,"%d %d %d %s",&mask[c],&cnt[c],&nmax[c],cname[c])!=4){fprintf(stderr,"read err\n");return 1;} }
    fclose(f);
    for(int s=0;s<NS;s++){ nsc[s]=0; for(int c=0;c<NC;c++) if(mask[c]&(1<<s)) sub_combos[s][nsc[s]++]=c; }
    out=fopen(outname,"w");
    dfs(0);
    fclose(out);
    fprintf(stderr,"allow=%d maxslot=%d nodes=%lld leaves=%lld\n",allow,MAXSLOT,nodes,leaves);
    return 0;
}
