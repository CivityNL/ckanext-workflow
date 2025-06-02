#!/bin/bash

CKAN_VERSION=2.9.9
INSTANCE=catalogus-lelystad
CONFIGURATION=/etc/ckan/${INSTANCE}/${INSTANCE}.ini
 . /usr/lib/ckan/ckan-${CKAN_VERSION}/venv/bin/activate

echo "getting roles"
ROLES=($(ckanapi action member_roles_list -c $CONFIGURATION | grep -oP '"value": "\K(.*)(?=")'))
ROLES=('no' "${ROLES[@]}")
echo "getting orgs"
ORGS=($(ckanapi action organization_list -c $CONFIGURATION | grep -oP '"\K(.*)(?=")'))
USERS=($(ckanapi action user_list -c $CONFIGURATION | grep -oP '"name": "\K(.*)(?=")'))

echo "ROLES $ROLES ${ROLES[*]} ${#ROLES[@]}"
echo "ORGS $ORGS ${ORGS[*]} ${#ORGS[@]}"
echo "USERS $USERS ${USERS[*]} ${#USERS[@]}"

N_O=${#ORGS[@]}
N_R=${#ROLES[@]}

N=$((N_O ** N_R))
echo $N

for (( i=0; i<$N; i++ ));
do
  user=
  for (( o=0; o<${#ORGS[@]}; o++ ));
  do
    r=$((i/(N_R ** o) % 4))
    user="${ORGS[$o]}-${ROLES[$r]}-$user"
  done
  echo "$user"
  if [[ ! " ${USERS[*]} " =~ .*" $user ".* ]]; then
    echo "creating user $user"
    ckanapi action user_create -c $CONFIGURATION email=$user@example.com name=$user password=Admin123!
  fi
  for (( o=0; o<${#ORGS[@]}; o++ ));
  do
    r=$((i/(N_R ** o) % 4))
    role=${ROLES[$r]}
    id=${ORGS[$o]}
    if [ $r -eq 0 ]; then
      echo "removing user $user as member of $id"
      ckanapi action organization_member_delete -c $CONFIGURATION id=$id username=$user
    else
      echo "adding user $user as $role of $id"
      ckanapi action organization_member_create -c $CONFIGURATION id=$id username=$user role=$role
    fi
  done
done